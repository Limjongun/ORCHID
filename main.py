import customtkinter as ctk
from ui.app import OrchidApp

def main():
    # Set the theme and color
    ctk.set_appearance_mode("Dark")
    # Using default blue theme, we will customize accents to sky blue in the UI
    ctk.set_default_color_theme("blue") 
    
    app = OrchidApp()
    app.mainloop()

if __name__ == "__main__":
    main()
