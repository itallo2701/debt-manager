import customtkinter as ctk
import sqlite3
from tkinter import StringVar

class DebtManagerApp(ctk.CTk):
    def __init__(self):
        """Inicializa a aplicação, cria a janela principal e conecta ao banco de dados."""
        super().__init__()
        self.title("Gerenciador de Dívidas e Créditos")
        self.geometry("500x400")

        # Conexão com o banco de dados
        self.conn = sqlite3.connect('debts.db')
        self.cursor = self.conn.cursor()

        # Inicializa banco de dados e interface
        self.setup_database()
        self.create_widgets()

    def setup_database(self):
        """Configura o banco de dados, criando as tabelas necessárias se elas não existirem."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                value REAL NOT NULL,
                reason TEXT NOT NULL,
                type TEXT NOT NULL,
                FOREIGN KEY (person_id) REFERENCES people(id)
            )
        ''')
        self.conn.commit()

    def create_widgets(self):
        """Cria todos os widgets da interface gráfica, como botões, entradas e listboxes."""
        # Notificação
        self.label_notification = ctk.CTkLabel(self, text="", text_color="green")

        # Entrada de Nome de Nova Pessoa
        ctk.CTkLabel(self, text="Adicionar Nova Pessoa:").grid(row=2, column=0, padx=10, pady=10)
        self.entry_new_person = ctk.CTkEntry(self)
        self.entry_new_person.grid(row=2, column=1, padx=10, pady=10)
        ctk.CTkButton(self, text="Adicionar", command=self.add_person).grid(row=2, column=2, padx=10, pady=10)

        # Seleção de Pessoa
        self.person_var = StringVar(self)
        self.person_menu = ctk.CTkOptionMenu(self, variable=self.person_var, values=[])
        self.person_menu.grid(row=3, column=1, padx=10, pady=10)
        ctk.CTkLabel(self, text="Selecionar Pessoa:").grid(row=3, column=0, padx=10, pady=10)
        self.update_person_list()

        # Entrada de Valor
        ctk.CTkLabel(self, text="Valor:").grid(row=4, column=0, padx=10, pady=10)
        self.entry_value = ctk.CTkEntry(self)
        self.entry_value.grid(row=4, column=1, padx=10, pady=10)

        # Entrada de Razão
        ctk.CTkLabel(self, text="Razão:").grid(row=5, column=0, padx=10, pady=10)
        self.entry_reason = ctk.CTkEntry(self)
        self.entry_reason.grid(row=5, column=1, padx=10, pady=10)

        # Botões para adicionar dívida e crédito
        ctk.CTkButton(self, text="Adicionar Dívida", command=self.add_debt).grid(row=6, column=0, padx=10, pady=10)
        ctk.CTkButton(self, text="Adicionar Crédito", command=self.add_credit).grid(row=6, column=1, padx=10, pady=10)

        # Listbox para exibir as dívidas e créditos
        self.listbox = ctk.CTkTextbox(self, height=100)
        self.listbox.grid(row=7, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Label para mostrar o saldo total
        self.label_balance = ctk.CTkLabel(self, text="Saldo Total: R$0.00", text_color="white")
        self.label_balance.grid(row=8, column=0, columnspan=3, pady=10)

        # Atualizar a listbox com os dados atuais
        self.update_listbox()

    def add_person(self):
        """Adiciona uma nova pessoa ao banco de dados e atualiza a lista de pessoas."""
        name = self.entry_new_person.get()
        if name:
            self.cursor.execute('INSERT INTO people (name) VALUES (?)', (name,))
            self.conn.commit()
            self.update_person_list()
            self.entry_new_person.delete(0, ctk.END)
            self.show_notification(f"{name} foi adicionada com sucesso!")

    def update_person_list(self):
        """Atualiza a lista de pessoas disponíveis no menu de seleção."""
        self.cursor.execute('SELECT name FROM people')
        people = [row[0] for row in self.cursor.fetchall()]
        self.person_var.set(people[0] if people else "")
        self.person_menu.configure(values=people)
        if people:
            self.person_menu.set(people[0])

    def add_debt_or_credit(self, value, reason, debt_type):
        """Registra uma nova dívida ou crédito no banco de dados."""
        person_name = self.person_var.get()
        self.cursor.execute('SELECT id FROM people WHERE name = ?', (person_name,))
        person_id = self.cursor.fetchone()[0]

        if debt_type == 'debt':
            # Ajusta créditos existentes antes de adicionar a nova dívida
            self.cursor.execute('SELECT id, value FROM debts WHERE person_id = ? AND type = "credit"', (person_id,))
            credit = self.cursor.fetchone()
            if credit:
                credit_id, credit_value = credit
                if credit_value > value:
                    new_credit_value = credit_value - value
                    self.cursor.execute('UPDATE debts SET value = ? WHERE id = ?', (new_credit_value, credit_id))
                    self.conn.commit()
                    self.update_listbox()
                    self.show_notification("Dívida adicionada com sucesso!")
                    return
                elif credit_value <= value:
                    value -= credit_value
                    self.cursor.execute('DELETE FROM debts WHERE id = ?', (credit_id,))
                    self.conn.commit()

        # Insere a nova dívida ou crédito no banco de dados
        self.cursor.execute('INSERT INTO debts (person_id, value, reason, type) VALUES (?, ?, ?, ?)',
                            (person_id, value, reason, debt_type))
        self.conn.commit()
        self.update_listbox()
        self.show_notification(f"{'Dívida' if debt_type == 'debt' else 'Crédito'} adicionada com sucesso!")

    def add_debt(self):
        """Captura os dados da interface e adiciona uma nova dívida."""
        value = float(self.entry_value.get())
        reason = self.entry_reason.get()
        self.add_debt_or_credit(value, reason, 'debt')

    def add_credit(self):
        """Captura os dados da interface e adiciona um novo crédito."""
        value = float(self.entry_value.get())
        reason = self.entry_reason.get()
        self.add_debt_or_credit(value, reason, 'credit')

    def get_all_debts_and_credits(self):
        """Recupera todas as dívidas e créditos do banco de dados."""
        self.cursor.execute('''
            SELECT p.name, d.value, d.reason, d.type 
            FROM debts d 
            JOIN people p ON d.person_id = p.id
        ''')
        return self.cursor.fetchall()

    def update_listbox(self):
        """Atualiza a listbox com todas as dívidas e créditos, e calcula o saldo total."""
        self.listbox.delete("1.0", ctk.END)
        total_credit = 0
        total_debt = 0

        for row in self.get_all_debts_and_credits():
            self.listbox.insert(ctk.END, f"{row[0]} - R${row[1]:.2f} - {row[2]} ({row[3]})\n")
            if row[3] == 'credit':
                total_credit += row[1]
            elif row[3] == 'debt':
                total_debt += row[1]

        total_balance = total_credit - total_debt
        balance_text = f"Saldo Total: R${total_balance:.2f} ({'Crédito' if total_balance > 0 else 'Dívida'})"
        self.label_balance.configure(text=balance_text)

    def show_notification(self, message):
        """Exibe uma notificação temporária na interface."""
        self.label_notification.configure(text=message)
        self.label_notification.grid(row=1, column=0, columnspan=3, pady=10)
        self.label_notification.after(3000, lambda: self.label_notification.grid_forget())

    def on_closing(self):
        """Fecha a conexão com o banco de dados e encerra a aplicação."""
        self.conn.close()
        self.destroy()

if __name__ == "__main__":
    app = DebtManagerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
