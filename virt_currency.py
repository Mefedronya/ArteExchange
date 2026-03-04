from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, timedelta
from typing import List, Optional, cast
import pyodbc
from jose import jwt, JWTError
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Рекомендуется выносить ключ в переменные окружения
SECRET_KEY = os.getenv("SECRET_KEY", "9c0ff8c9299ea0832b4b0c6361a4324ac84159806dcc9700decad80de6f219c9")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# ================= Модели =================

class currencyItem(BaseModel):
    id: Optional[int] = None
    quantity: int
    get_Time: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class currcreate(BaseModel):
    quantity: int

class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str = Field(..., max_length=40, description="Имя пользователя, максимум 40 символов")
    password: str = Field(..., min_length=6, max_length=72, description="Пароль, минимум 6 символов")
    first_name: Optional[str] = Field(None, max_length=72, description="Имя, максимум 80 символов")
    surname: Optional[str] = Field(None, max_length=72, description="Фамилия, максимум 80 символов")

    @field_validator('username')
    @classmethod
    def username_must_not_be_empty(cls, v):
        if not v or not v.isalnum():
            raise ValueError('Username должен содержать только буквы и цифры')
        return v
    
    #@field_validator('password')
    #@classmethod
    ##byte_length = len(v.encode('utf-8'))
     #if byte_length > 72:
        # Можно добавить предупреждение в лог, но не выбрасывать исключение
        #print(f"Предупреждение: пароль слишком длинный ({byte_length} байт), будет обрезан bcrypt")
     #return v 

class UserResponse(BaseModel):
    id: int
    username: str
    first_name: Optional[str] = None
    surname: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class userLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

# ================= Безопасность =================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")  
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    try:        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, first_name, surname, created_at FROM Accounts WHERE username = ?",
                (token_data.username,)
            )
            user_row = cursor.fetchone()
            
            if user_row is None:
                raise credentials_exception
            
            return {
                "id": user_row[0],
                "username": user_row[1],
                "first_name": user_row[2],
                "surname": user_row[3],
                "created_at": user_row[4]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {e}")

# ================= База данных =================

class databaseManager:
    def __init__(self):
        self.server = 'DESKTOP-P5B9MPU\\SQLEXPRESS'
        self.database = 'it_planet'
        self.connection_string = (f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                                  f"SERVER={self.server};"
                                  f"DATABASE={self.database};"
                                  "Trusted_Connection=yes;")
        
    def get_connection(self):
        return pyodbc.connect(self.connection_string) 

db_manager = databaseManager()
# Проверка подключения при старте (опционально)
try:
    db_manager.get_connection().close()
except Exception as e:
    print(f"Warning: Could not connect to DB at startup: {e}")

# ================= Ручки =================

@app.get("/")
def read_root():
    return {"message": "Welcome to the virtual currency API"}

@app.post("/register")
def register_user(user: UserCreate):
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Проверяем, не занят ли username
            cursor.execute("SELECT id FROM Accounts WHERE username = ?", (user.username,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким именем уже существует"
                )
    
            # 2. Хешируем пароль (ОДИН РАЗ)
            try:
                hashed_password = get_password_hash(user.password)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ошибка пароля: {str(e)}"
                )
    
            # 3. Вставляем пользователя
            cursor.execute(
                """INSERT INTO Accounts (username, password_hash, first_name, surname) 
                   OUTPUT INSERTED.id, INSERTED.username, INSERTED.first_name, INSERTED.surname, INSERTED.created_at
                   VALUES (?, ?, ?, ?)""",
                (user.username, hashed_password, user.first_name, user.surname)
            )
            new_user = cursor.fetchone()
            conn.commit()

            new_user = cast(tuple, new_user)  

            return UserResponse(
                id=new_user[0],
                username=new_user[1],
                first_name=new_user[2],
                surname=new_user[3],
                created_at=new_user[4]
            )
            
    except HTTPException:
        # ВАЖНО: Пробрасываем наши ошибки (400, 401) без изменений
        raise
    except pyodbc.Error as db_error:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(db_error)}")
    except Exception as e:
        # Только реальные непредвиденные ошибки идут сюда как 500
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.post("/token", response_model=Token)
async def login(credentials: OAuth2PasswordRequestForm = Depends()):
    try: 
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash FROM Accounts WHERE username = ?", 
                (credentials.username,)
            )
            user_row = cursor.fetchone()
            
            if not user_row or not verify_password(credentials.password, user_row[2]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверное имя пользователя или пароль",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token_ = create_access_token(
                data={"sub": user_row[1]}, 
                expires_delta=access_token_expires) 
            
            return Token(access_token=access_token_, token_type="bearer")
            
    except pyodbc.Error as db_error:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(db_error)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.get("/user/currency", response_model=List[currencyItem])
def get_user_currency():
    try:
        with databaseManager().get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, quantity, get_Time FROM Currency")
            rows = cursor.fetchall()

            return [
                currencyItem(id=row[0], quantity=row[1], get_Time=row[2])
                for row in rows
            ]
    except pyodbc.Error as db_error:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(db_error)}")
    except HTTPException:
        raise
    except Exception as e:
        # Нейтральное сообщение об ошибке
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

class UserSchema(BaseModel):
    username: str
    balance: float

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)