import tkinter as tk
import uuid
import hashlib

def gerar_id_unico():
    mac = uuid.getnode()
    mac_str = ':'.join(['{:02x}'.format((mac >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])
    return hashlib.sha256(mac_str.encode()).hexdigest()

def mostrar_id():
    id_unico = gerar_id_unico()
    texto_id.config(state='normal')
    texto_id.delete("1.0", tk.END)
    texto_id.insert(tk.END, id_unico)
    texto_id.config(state='disabled')

app = tk.Tk()
app.title("Gerador de Código de Ativação")
app.geometry("500x200")
app.resizable(False, False)

# Rótulo
rotulo = tk.Label(app, text="Seu código de ativação é:", font=("Arial", 14))
rotulo.pack(pady=10)

# Campo de texto para exibir o ID
texto_id = tk.Text(app, height=2, font=("Courier", 12), wrap="none", state='disabled')
texto_id.pack(padx=20, pady=5, fill='x')

# Botão
botao_gerar = tk.Button(app, text="Gerar Código", font=("Arial", 12), command=mostrar_id)
botao_gerar.pack(pady=10)

app.mainloop()
import tkinter as tk
import uuid
import hashlib

def gerar_id_unico():
    mac = uuid.getnode()
    mac_str = ':'.join(['{:02x}'.format((mac >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])
    return hashlib.sha256(mac_str.encode()).hexdigest()

def mostrar_id():
    id_unico = gerar_id_unico()
    texto_id.config(state='normal')
    texto_id.delete("1.0", tk.END)
    texto_id.insert(tk.END, id_unico)
    texto_id.config(state='disabled')

app = tk.Tk()
app.title("Gerador de Código de Ativação")
app.geometry("500x200")
app.resizable(False, False)

# Rótulo
rotulo = tk.Label(app, text="Seu código de ativação é:", font=("Arial", 14))
rotulo.pack(pady=10)

# Campo de texto para exibir o ID
texto_id = tk.Text(app, height=2, font=("Courier", 12), wrap="none", state='disabled')
texto_id.pack(padx=20, pady=5, fill='x')

# Botão
botao_gerar = tk.Button(app, text="Gerar Código", font=("Arial", 12), command=mostrar_id)
botao_gerar.pack(pady=10)

app.mainloop()
