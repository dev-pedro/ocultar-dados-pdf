import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from ocultar_dados import ocultar_fatura

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ocultar Dados Sensíveis em PDF")
        self.geometry("600x420")
        self.resizable(False, False)

        self.input_file = ""
        self.output_dir = os.path.join(self.get_documents_folder(), "pdf_oculto")

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Title
        self.title_label = ctk.CTkLabel(self, text="Ocultar Dados Sensíveis (Faturas)", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10))

        # Seleção de Arquivo
        self.file_label = ctk.CTkLabel(self, text="Arquivo PDF:")
        self.file_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.file_entry = ctk.CTkEntry(self, placeholder_text="Nenhum arquivo selecionado...")
        self.file_entry.grid(row=2, column=0, padx=(20, 10), pady=(5, 10), sticky="ew")
        
        self.btn_browse = ctk.CTkButton(self, text="Procurar...", command=self.browse_file)
        self.btn_browse.grid(row=2, column=1, padx=(0, 20), pady=(5, 10))

        # Texto a ignorar
        self.ignore_label = ctk.CTkLabel(self, text="Texto da linha a ignorar (opcional):")
        self.ignore_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.ignore_entry = ctk.CTkEntry(self, placeholder_text="Ex: 24 FEV Alura - NuPay - Parcela 1/12 R$ 87,20")
        self.ignore_entry.grid(row=4, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")

        # Botão Processar
        self.btn_process = ctk.CTkButton(self, text="Processar PDF", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.process_pdf)
        self.btn_process.grid(row=5, column=0, columnspan=2, padx=20, pady=(30, 5), sticky="ew")

        # Log/Status
        self.status_label = ctk.CTkLabel(self, text="Aguardando...", text_color="gray")
        self.status_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(5, 0))

        # Apenas container para o link no grid, sera instanciado depois
        self.link_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.link_frame.grid(row=7, column=0, columnspan=2, pady=(0, 10))
        self.link_button = None

    def get_documents_folder(self):
        home = os.path.expanduser("~")
        docs_pt = os.path.join(home, "Documentos")
        docs_en = os.path.join(home, "Documents")
        if os.path.exists(docs_pt) and not os.path.exists(docs_en):
            return docs_pt
        return docs_en

    def open_output_folder(self):
        if os.path.exists(self.output_dir):
            os.startfile(self.output_dir)

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecione o PDF",
            filetypes=(("PDF Files", "*.pdf"), ("All Files", "*.*"))
        )
        if filepath:
            self.input_file = filepath
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, filepath)
            self.status_label.configure(text="Pronto para processar.", text_color="gray")
            if self.link_button:
                self.link_button.destroy()
                self.link_button = None

    def process_pdf(self):
        if not self.input_file or not os.path.exists(self.input_file):
            messagebox.showwarning("Aviso", "Por favor, selecione um arquivo PDF válido primeiro.")
            return

        texto_ignorar = self.ignore_entry.get()

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        filename = os.path.basename(self.input_file)
        output_file = os.path.join(self.output_dir, f"oculto_{filename}")

        self.status_label.configure(text=f"Processando...", text_color="orange")
        self.btn_process.configure(state="disabled")
        if self.link_button:
            self.link_button.destroy()
            self.link_button = None

        # Executar na thread
        threading.Thread(target=self._run_ocultar, args=(self.input_file, output_file, texto_ignorar), daemon=True).start()

    def _run_ocultar(self, input_pdf, output_pdf, texto_ignorar):
        try:
            ocultar_fatura(input_pdf, output_pdf, texto_ignorar)
            self.after(0, self._process_success, output_pdf)
        except Exception as e:
            self.after(0, self._process_error, str(e))

    def _process_success(self, output_pdf):
        self.status_label.configure(text="Concluído com sucesso!", text_color="green")
        
        # Cria o botao link apenas depois do sucesso
        if not self.link_button:
            self.link_button = ctk.CTkButton(self.link_frame, text=f"Abrir Pasta: {self.output_dir}", fg_color="transparent", text_color="#1f538d", hover_color="#89CFF0", font=ctk.CTkFont(underline=True), command=self.open_output_folder)
            self.link_button.pack()
            
        self.btn_process.configure(state="normal")
        self.input_file = ""
        self.file_entry.delete(0, "end")

    def _process_error(self, error_msg):
        self.status_label.configure(text="Erro ao processar PDF.", text_color="red")
        self.btn_process.configure(state="normal")
        messagebox.showerror("Erro", f"Ocorreu um erro ao processar o PDF:\n{error_msg}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
