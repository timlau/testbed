import tkinter as tk

app = tk.Tk()
app.geometry("800x600")
app.title("My TKInter GUI")
label = tk.Label(app,text="Hallo World",font=("Default",16))
label.pack(padx=20,pady=20)

app.mainloop()