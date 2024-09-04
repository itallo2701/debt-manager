import customtkinter as ctk
import sqlite3
from tkinter import StringVar

# Conectar ao banco de dados SQLite (será criado se não existir)
conn = sqlite3.connect('debts.db')
cursor = conn.cursor()

# Criar as tabelas se não existirem
cursor.execute('''
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        value REAL NOT NULL,
        reason TEXT NOT NULL,
        type TEXT NOT NULL,
        FOREIGN KEY (person_id) REFERENCES people(id)
    )
''')
conn.commit()

# Função para adicionar uma nova pessoa
def add_person():
    name = entry_new_person.get()
    if name:
        cursor.execute('''
            INSERT INTO people (name) VALUES (?)
        ''', (name,))
        conn.commit()
        update_person_list()
        entry_new_person.delete(0, ctk.END)
        show_notification(f"{name} foi adicionada com sucesso!")

# Função para atualizar a lista de pessoas no CTkOptionMenu
def update_person_list():
    cursor.execute('SELECT name FROM people')
    people = [row[0] for row in cursor.fetchall()]
    person_var.set(people[0] if people else "")
    person_menu.configure(values=people)
    if people:
        person_menu.set(people[0])

# Função para adicionar dívida/crédito
def add_debt_or_credit(value, reason, debt_type):
    person_name = person_var.get()
    cursor.execute('SELECT id FROM people WHERE name = ?', (person_name,))
    person_id = cursor.fetchone()[0]

    if debt_type == 'debt':
        # Verificar se a pessoa te deve algo
        cursor.execute('''
            SELECT id, value FROM debts WHERE person_id = ? AND type = 'credit'
        ''', (person_id,))
        credit = cursor.fetchone()
        if credit:
            credit_id, credit_value = credit
            if credit_value > value:
                new_credit_value = credit_value - value
                cursor.execute('UPDATE debts SET value = ? WHERE id = ?', (new_credit_value, credit_id))
                conn.commit()
                update_listbox()
                show_notification("Dívida adicionada com sucesso!")
                return
            elif credit_value <= value:
                value -= credit_value
                cursor.execute('DELETE FROM debts WHERE id = ?', (credit_id,))
                conn.commit()

    cursor.execute('''
        INSERT INTO debts (person_id, value, reason, type) VALUES (?, ?, ?, ?)
    ''', (person_id, value, reason, debt_type))
    conn.commit()
    update_listbox()
    show_notification(f"{'Dívida' if debt_type == 'debt' else 'Crédito'} adicionada com sucesso!")

# Função para adicionar nova dívida
def add_debt():
    value = float(entry_value.get())
    reason = entry_reason.get()
    add_debt_or_credit(value, reason, 'debt')

# Função para adicionar novo crédito
def add_credit():
    value = float(entry_value.get())
    reason = entry_reason.get()
    add_debt_or_credit(value, reason, 'credit')

# Função para exibir todas as dívidas/créditos
def get_all_debts_and_credits():
    cursor.execute('''
        SELECT p.name, d.value, d.reason, d.type 
        FROM debts d 
        JOIN people p ON d.person_id = p.id
    ''')
    return cursor.fetchall()

def update_listbox():
    listbox.delete("1.0", ctk.END) 
    total_credit = 0
    total_debt = 0

    for row in get_all_debts_and_credits():
        listbox.insert(ctk.END, f"{row[0]} - R${row[1]:.2f} - {row[2]} ({row[3]})\n")
        if row[3] == 'credit':
            total_credit += row[1]
        elif row[3] == 'debt':
            total_debt += row[1]

    total_balance = total_credit - total_debt
    balance_text = f"Saldo Total: R${total_balance:.2f} ({'Crédito' if total_balance > 0 else 'Dívida'})"
    label_balance.configure(text=balance_text)  # Usando 'configure' em vez de 'config'

# Função para mostrar uma notificação temporária
def show_notification(message):
    label_notification.configure(text=message)
    label_notification.grid(row=1, column=0, columnspan=3, pady=10)
    label_notification.after(3000, lambda: label_notification.grid_forget())

# Criar a janela principal
app = ctk.CTk()
app.title("Gerenciador de Dívidas e Créditos")
app.geometry("500x400")

# Notificação
label_notification = ctk.CTkLabel(app, text="", text_color="green")

# Entrada de Nome de Nova Pessoa
label_new_person = ctk.CTkLabel(app, text="Adicionar Nova Pessoa:")
label_new_person.grid(row=2, column=0, padx=10, pady=10)
entry_new_person = ctk.CTkEntry(app)
entry_new_person.grid(row=2, column=1, padx=10, pady=10)
button_add_person = ctk.CTkButton(app, text="Adicionar", command=add_person)
button_add_person.grid(row=2, column=2, padx=10, pady=10)

# Seleção de Pessoa
person_var = StringVar(app)
person_menu = ctk.CTkOptionMenu(app, variable=person_var, values=[])
person_menu.grid(row=3, column=1, padx=10, pady=10)
label_person = ctk.CTkLabel(app, text="Selecionar Pessoa:")
label_person.grid(row=3, column=0, padx=10, pady=10)
update_person_list()

# Entrada de Valor
label_value = ctk.CTkLabel(app, text="Valor:")
label_value.grid(row=4, column=0, padx=10, pady=10)
entry_value = ctk.CTkEntry(app)
entry_value.grid(row=4, column=1, padx=10, pady=10)

# Entrada de Razão
label_reason = ctk.CTkLabel(app, text="Razão:")
label_reason.grid(row=5, column=0, padx=10, pady=10)
entry_reason = ctk.CTkEntry(app)
entry_reason.grid(row=5, column=1, padx=10, pady=10)

# Botão para adicionar dívida
button_add_debt = ctk.CTkButton(app, text="Adicionar Dívida", command=add_debt)
button_add_debt.grid(row=6, column=0, padx=10, pady=10)

# Botão para adicionar crédito
button_add_credit = ctk.CTkButton(app, text="Adicionar Crédito", command=add_credit)
button_add_credit.grid(row=6, column=1, padx=10, pady=10)

# Listbox para exibir as dívidas e créditos
listbox = ctk.CTkTextbox(app, height=100)
listbox.grid(row=7, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# Label para mostrar o saldo total
label_balance = ctk.CTkLabel(app, text="Saldo Total: R$0.00", text_color="white")
label_balance.grid(row=8, column=0, columnspan=3, pady=10)

# Atualizar a listbox com os dados atuais
update_listbox()

# Iniciar o loop principal da aplicação
app.mainloop()

# Fechar a conexão com o banco de dados ao encerrar o aplicativo
conn.close()
