from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.button import MDRaisedButton

import requests


class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.username = MDTextField(
            text="Логин",
            pos_hint={"center_x": 0.5, "center_y": 0.6},
            size_hint_x = 0.6
        )

        self.password = MDTextField(
            text="Пароль",
            password=True,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint_x = 0.6
        )

        login_button = MDRaisedButton(
            text="Войти",
            pos_hint={"center_x": 0.35, "center_y": 0.4},
            on_release=self.login
        )

        register_button = MDRaisedButton(
            text="Регистрация",
            pos_hint={"center_x": 0.6, "center_y": 0.4},
            on_release=self.go_register
        )

        self.message_label = MDLabel(
            text="",
            halign="center",
            pos_hint={"center_x": 0.5, "center_y": 0.3}
        )

        self.add_widget(self.username)
        self.add_widget(self.password)
        self.add_widget(login_button)
        self.add_widget(register_button)
        self.add_widget(self.message_label)
    def login(self, instance):
        try:
            response = requests.post("http://127.0.0.1:8000/login", json={
                "username": self.username.text,
                "password": self.password.text
            })
            if response.status_code == 200:
                self.manager.current = "main"
            else:
                self.message_label.text = "Неверный логин или пароль"
        except Exception as e:
            self.message_label.text = f"Ошибка: {e}"

    def go_register(self, instance):
        if self.manager:
            self.manager.current = "register"

class RegisterScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.username = MDTextField(
            hint_text="Логин",
            pos_hint={"center_x": 0.5, "center_y": 0.65},
            size_hint_x=0.4
        )

        self.password = MDTextField(
            hint_text="Пароль",
            password=True,
            pos_hint={"center_x": 0.5, "center_y": 0.55},
            size_hint_x=0.4
        )

        register_button = MDRaisedButton(
            text="Зарегистрироваться",
            pos_hint={"center_x": 0.6, "center_y": 0.25},
            on_release=self.register
        )

        self.surname = MDTextField(
            hint_text="Фамилия",
            pos_hint={"center_x": 0.5, "center_y": 0.45},
            size_hint_x=0.4
        )

        self.last_name = MDTextField(
            hint_text="Имя",
            pos_hint={"center_x": 0.5, "center_y": 0.35},
            size_hint_x=0.4
        )

        back_button = MDRaisedButton(
            text="Назад",
            pos_hint={"center_x": 0.35, "center_y": 0.25},
            on_release=self.go_back
        )

        self.message_label = MDLabel(
            text="",
            halign="center",
            pos_hint={"center_x": 0.5, "center_y": 0.28}
        )

        self.add_widget(self.username)
        self.add_widget(self.password)
        self.add_widget(register_button)
        self.add_widget(back_button)
        self.add_widget(self.message_label)
        self.add_widget(self.surname)
        self.add_widget(self.last_name)

    def register(self, instance):
        try:
            response = requests.post("http://127.0.0.1:8000/register", json={
                "username": self.username.text,
                "password": self.password.text
            })

            if response.status_code == 201:
                self.message_label.text = "Регистрация успешна!"
            else:
                self.message_label.text = "Ошибка регистрации"

        except Exception as e:
            self.message_label.text = f"Ошибка: {e}"

    def go_back(self, instance):
        self.manager.current = "login"

class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        label = MDLabel(text="Ваша валюта:",
                         halign="center",
                         theme_text_color="Primary",
                         pos_hint={"center_x": 0.2, "center_y": 0.5})

        self.label_currency = MDLabel(text="?",
                                     halign="center",
                                     theme_text_color="Primary",
                                     pos_hint={"center_x": 0.5, "center_y": 0.5})

        self.add_widget(label)
        self.add_widget(self.label_currency)
        self.get_currency()

    def get_currency(self):
        try:
            response = requests.get("http://127.0.0.1:8000/user/currency")
            data = response.json()
            if data:
                currency = data[0].get('quantity')
                self.label_currency.text = str(currency)
            else:
                self.label_currency.text = "Нет данных"
        except Exception:
            self.label_currency.text = "Ошибка при получении данных"

class CurrencyApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"

        sm = ScreenManager()
        
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(MainScreen(name="main"))
        
        sm.current = "login"
        
        return sm
            

if __name__ == "__main__":
    CurrencyApp().run()