import customtkinter as ctk
from src.core.supabase_client import SupabaseManager
import threading

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, on_success_callback):
        super().__init__()
        
        self.on_success = on_success_callback
        self.supabase = SupabaseManager()
        
        # Window Setup
        self.title("WhisperFlow - Connexion")
        self.geometry("400x580")
        self.resizable(False, False)
        self.attributes('-topmost', True)
        
        # UI Styling
        self.grid_columnconfigure(0, weight=1)
        
        # Logo / Title
        self.label_title = ctk.CTkLabel(self, text="WhisperFlow", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.grid(row=0, column=0, padx=20, pady=(40, 10))
        
        self.label_subtitle = ctk.CTkLabel(self, text="Connectez-vous pour commencer", text_color="gray")
        self.label_subtitle.grid(row=1, column=0, padx=20, pady=(0, 30))
        
        # Form
        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email", width=300, height=45)
        self.email_entry.grid(row=2, column=0, padx=20, pady=10)
        
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Mot de passe", show="*", width=300, height=45)
        self.password_entry.grid(row=3, column=0, padx=20, pady=10)
        
        # Buttons
        self.login_button = ctk.CTkButton(self, text="Se connecter", command=self.handle_login, width=300, height=45, fg_color="#0b1a78")
        self.login_button.grid(row=4, column=0, padx=20, pady=(30, 10))
        
        self.signup_button = ctk.CTkButton(self, text="Créer un compte", command=self.handle_signup, width=300, height=45, fg_color="transparent", border_width=1)
        self.signup_button.grid(row=5, column=0, padx=20, pady=10)

        # Forgot password
        self.forgot_password_button = ctk.CTkButton(
            self, text="Mot de passe oublié ?", command=self.handle_forgot_password,
            width=300, height=25, fg_color="transparent", hover_color="#1a1a2e",
            text_color="gray", font=ctk.CTkFont(size=12, underline=True),
        )
        self.forgot_password_button.grid(row=6, column=0, padx=20, pady=(0, 5))

        # Error Label
        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.grid(row=7, column=0, padx=20, pady=10)

    def handle_login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        if not email or not password:
            self.error_label.configure(text="Veuillez remplir tous les champs")
            return
            
        self.login_button.configure(state="disabled", text="Connexion...")
        threading.Thread(target=self._login_thread, args=(email, password), daemon=True).start()

    def _login_thread(self, email, password):
        success = self.supabase.login(email, password)
        if success:
            self.after(0, self.on_success)
            self.after(0, self.destroy)
        else:
            self.after(0, lambda: self.error_label.configure(text="Email ou mot de passe incorrect"))
            self.after(0, lambda: self.login_button.configure(state="normal", text="Se connecter"))

    def handle_signup(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        if not email or not password:
            self.error_label.configure(text="Veuillez remplir tous les champs")
            return
            
        self.signup_button.configure(state="disabled", text="Création...")
        threading.Thread(target=self._signup_thread, args=(email, password), daemon=True).start()

    def _signup_thread(self, email, password):
        success = self.supabase.signup(email, password)
        if success:
            self.after(0, lambda: self.error_label.configure(text="Compte créé ! Vérifiez vos emails.", text_color="green"))
            self.after(0, lambda: self.signup_button.configure(state="normal", text="Créer un compte"))
        else:
            self.after(0, lambda: self.error_label.configure(text="Erreur lors de la création du compte", text_color="red"))
            self.after(0, lambda: self.signup_button.configure(state="normal", text="Créer un compte"))

    def handle_forgot_password(self):
        email = self.email_entry.get()

        if not email:
            self.error_label.configure(text="Entrez votre email pour réinitialiser le mot de passe", text_color="red")
            return

        self.forgot_password_button.configure(state="disabled", text="Envoi...")
        threading.Thread(target=self._forgot_password_thread, args=(email,), daemon=True).start()

    def _forgot_password_thread(self, email):
        success = self.supabase.reset_password_for_email(email)
        if success:
            self.after(0, lambda: self.error_label.configure(text="Email de réinitialisation envoyé !", text_color="green"))
        else:
            self.after(0, lambda: self.error_label.configure(text="Erreur lors de l'envoi de l'email", text_color="red"))
        self.after(0, lambda: self.forgot_password_button.configure(state="normal", text="Mot de passe oublié ?"))
