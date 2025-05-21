import sys
import threading
from pprint import pprint
from tkinter import *
from tkinter.ttk import Combobox, Checkbutton
from xml.sax.handler import property_interning_dict

from PIL import ImageTk, Image

from db import Database
from classes.core import *
from tkinter import filedialog, messagebox, ttk
import pandas as pd


# Função para obter caminho do recurso (usada no PyInstaller)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller cria uma pasta temporária
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class PerkonsInfoCam:
    def __init__(self):
        self.btn_exportar_resultado = None
        self.btn_parar = None
        self.table = None
        self.text_area = None
        self.combo_cameras = None
        self.combo_pontos = None
        self.check = None
        self.todas_as_cameras = None
        self.db = Database()
        self.handlecam = HandleInfoCamera(self.db)
        self.site_data = SiteData(self.db)
        self.stop = False
        self.verifica_acesso_vpn()
        self.window = Tk()
        self.window.title("Perkons Info Cam")
        self.window.resizable(1, 1)
        self.window.geometry("1360x1000")
        self.window.config(bg="orange")
        self.frame_menu = Frame(self.window, bg="#cccccc")
        self.frame_menu.pack(side="left", fill="y")
        self.frame_result = Frame(self.window, bg="#eeeeee")
        self.frame_result.pack(side="right", fill="both", expand=True)

        # Carregar dados necessários
        info_sites = SiteData(self.db)
        self.sites_nomes = info_sites.get_list_sites_names()
        self.sites = info_sites.get_list_sites()

        self.create_interface()
        self.window.mainloop()

    def create_interface(self):
        """Cria a "interface" gráfica da aplicação."""

        # Criar Menu
        self.create_menu()

        # Criar Resultado
        self.create_result_area()

    def create_menu(self):
        """Cria o menu lateral da aplicação."""

        # Logo
        img_logo = Image.open(resource_path("imagens/logo.png"))
        img_logo_tk = ImageTk.PhotoImage(image=img_logo)
        Label(self.frame_menu, image=img_logo_tk, bg=self.frame_menu.cget("bg")).pack(
            pady=20
        )
        self.window.image_logo = img_logo_tk  # Prevenir garbage collection

        # Check Box para executar todas as cameras
        self.todas_as_cameras = IntVar()
        self.check = Checkbutton(
            self.frame_menu,
            text="Atualizar Todas as câmeras?",
            variable=self.todas_as_cameras,
        )
        self.check.pack(fill="x", padx=20, pady=10)

        # ComboBox para seleção do ponto
        self.criar_label(self.frame_menu, "ESCOLHA O PONTO")
        self.combo_pontos = Combobox(self.frame_menu, font="verdana 12", height=3)
        self.combo_pontos["values"] = self.sites_nomes
        self.combo_pontos.current(0)
        self.combo_pontos.bind("<<ComboboxSelected>>", self.filtra_camera),
        self.combo_pontos.bind("<Return>", self.filtra_camera),
        self.combo_pontos.pack(fill="x", pady=5, padx=20)

        # ComboBox para selecionar a câmera
        self.criar_label(self.frame_menu, "ESCOLHA A CÂMERA")
        self.combo_cameras = Combobox(self.frame_menu, font="verdana 12", height=5)
        self.combo_cameras.pack(fill="x", pady=5, padx=20)

        # Botões de ação
        self.criar_label(self.frame_menu, "ESCOLHA A AÇÃO")

        botoes = [
            ("Atualizar Seriais", self.thread_atualizar_seriais),
            ("Atualizar Firmwares", self.thread_atualizar_firmwares),
            ("Atualizar Modelo Câmeras", self.thread_atualizar_modelos),
            ("Reiniciar Câmeras", self.thread_configurar_reset),
            ("Consultar Auto Register", self.thread_consulta_autoregister),
            ("Configurar Auto Register", self.thread_configurar_autoregister),
            ("Configurar Auto Maintain", self.thread_configurar_auto_maintain),
            ("Configurar Fontes", self.thread_configurar_fontes),
            ("Consultar Display da Câmera", self.thread_consultar_display),
            ("Visualizar Snapshot", self.thread_visualizar_snapshot),
            ("Listar Roteadores offline", self.thread_roteador_offline),
            ("Listar Câmeras Offline", self.thread_lista_cameras_offline),
            ("Exportar Lista de Câmeras", self.thread_exportar_lista),
        ]

        for texto, comando in botoes:
            self.criar_botao(self.frame_menu, texto, comando)

    def create_result_area(self):
        """Cria a área de exibição dos resultados."""
        self.criar_label(self.frame_result, "RESULTADO DA CONSULTA", font_size=20)

        self.btn_parar = Button(self.frame_result, text="Parar Execução", command=self.para_execucao, font="verdana 15")
        self.btn_parar.pack(fill="x", padx=10, pady=10)
        self.btn_parar.config(state='disabled')

        self.btn_exportar_resultado = Button(self.frame_result, text="Exportar resultado",
                                             command=self.exportar_resultado, font="verdana 15")
        self.btn_exportar_resultado.pack(fill='x', padx=10, pady=10)
        self.btn_exportar_resultado.config(state='disabled')

        style = ttk.Style()
        style.theme_use("clam")

        self.cria_tabela(["Ponto", "Nome da Câmera","Informação"])

    # ===================== Funções Auxiliares ======================== #

    def cria_tabela(self, columns: list[str]):

        if self.table:
            self.table.destroy()

        self.table = ttk.Treeview(self.frame_result, selectmode="extended")
        self.table['columns'] = columns

        # Formatando colunas e Cabeçalhos
        self.table.column('#0', width=0, stretch=False)
        for column in columns:
            # Defini coluna
            self.table.column(column, width=100, stretch=True)
            # Defini Cabeçalho
            self.table.heading(column, text=column, anchor='w')

        # Configurando ScrollBar
        vsb = ttk.Scrollbar(self.frame_result, orient="vertical", command=self.table.yview)
        vsb.pack(side='right', fill='y')
        self.table.configure(yscrollcommand=vsb.set)

        self.table.pack(expand=True, fill='both', padx=10, pady=10)

    @staticmethod
    def criar_label(parent, text, font_size=15):
        """Cria e adiciona um rótulo ao frame especificado."""
        Label(
            parent,
            text=text,
            fg="#3b3b3b",
            font=f"verdana {font_size} bold",
            bg=parent.cget("bg"),
        ).pack(pady=5, padx=20, anchor="w")

    @staticmethod
    def criar_botao(parent, text, command):
        """Cria e adiciona um botão ao frame especificado."""
        Button(parent, text=text, font="verdana 12", command=command).pack(
            fill="x", pady=5, padx=20
        )

    @staticmethod
    def verifica_acesso_vpn():
        """
        Verifica se o IP alvo está "online" e, se não estiver, impede a execução do "software".
        """
        if not NetworkUtils.verificar_ping("10.1.5.158"):
            messagebox.showerror(
                "VPN Desconectada", "Favor realizar a conexão com a VPN PERKONS!"
            )
            exit(1)
        else:
            messagebox.showinfo("VPN Conectada", "Você está conectado a VPN !")

    def filtra_camera(self, event):
        """Função associada ao evento de onchanged do combobox pontos"""
        cameras_site = [
            "Todas as Câmeras",
        ]
        ponto = self.combo_pontos.get()
        cameras = self.db.selecionar_ponto(ponto)
        for camera in cameras:
            cameras_site.append(camera[5])

        self.combo_cameras["values"] = cameras_site
        self.combo_cameras.current(0)

    def executa_visualizar_snapshot(self):
        cameras = self.db
        camera_selecionada = self.combo_cameras.get()

        if camera_selecionada != "Todas as Câmeras":
            camera = cameras.selecionar_camera(camera_selecionada)
            endereco_camera = f'{camera[0][4]}:{camera[0][8]}'
            url_imagem = self.handlecam.get_snapshot(endereco_camera,
                                                     f"imagens/snapshot/{camera[0][4]}_{camera[0][8]}.jpg",
                                                     params={'channel': 1})
            self.show_image_dialog(url_imagem)
        else:
            messagebox.showerror("Opção Inválida",
                                 "Não é possivel selecionar todas as câmeras ou não selecionar nenhuma camera.")

    @staticmethod
    def show_image_dialog(image_path):
        """Shows an image in a Tkinter dialog."""
        try:
            # Open the image using PIL
            image = Image.open(image_path)
            resized_image = image.resize((1366, 768))
            # Convert the image to Tkinter-compatible format
            photo = ImageTk.PhotoImage(resized_image)

            # Create a Toplevel window for the dialog
            dialog = Toplevel()
            dialog.title("Image Dialog")

            # Create a Label to display the image
            image_label = Label(dialog, image=photo)
            image_label.image = photo  # Keep a reference to the image to prevent garbage collection
            image_label.pack()

            # Add a button to close the dialog
            close_button = Button(dialog, text="Close", command=dialog.destroy)
            close_button.pack()

        except FileNotFoundError:
            messagebox.showerror("Error", "Image file not found.")
        except Exception as e:
            messagebox.showerror("Câmera Offline", f"An error occurred: {e}")

    def para_execucao(self):
        self.stop = True

    def exportar_resultado(self):
        tabela = []
        for item in self.table.get_children():
            values = self.table.item(item, 'values')
            tabela.append(values)

        colunas = [self.table.heading(col)['text'] for col in self.table['columns']]
        df = pd.DataFrame(tabela, columns=colunas)
        caminho_padrao = os.getcwd()
        caminho = filedialog.askdirectory(initialdir=caminho_padrao)
        arquivo = os.path.join(caminho, "tabela.xlsx")
        df.to_excel(arquivo, index=False)
        messagebox.showinfo("Informação", "Resultado exportado com sucesso.")

    @staticmethod
    def exporta_lista():
        """
        Extrai dados do banco de dados, gerando uma lista com as informações das câmeras
        """
        try:
            caminho_padrao = os.getcwd()
            caminho = filedialog.askdirectory(initialdir=caminho_padrao)
            arquivo = os.path.join(caminho, "lista.xlsx")
            db = Database()
            cameras = db.selecionar_todas_cameras()
            df = pd.DataFrame(
                cameras,
                columns=[
                    "id",
                    "ponto",
                    "regiao",
                    "nome_ponto",
                    "ip",
                    "nome_camera",
                    "firmware",
                    "serial",
                    "porta",
                    "modelo",
                    "latitude",
                    "longitude",
                    "atualizado",
                ],
            )
            df["atualizado"] = pd.to_datetime(df["atualizado"]).dt.strftime(
                "%d/%m/%Y %H:%M:%S"
            )
            df.to_excel(arquivo)
        except os.error as e:
            print("Error: " + e)

        messagebox.showinfo("Informação", "Lista de câmeras gerada com sucesso!")

    # ====================== FUNÇÕES DE CONSULTA ====================== #

    def atualizar_seriais(self):
        """Realiza consulta de Seriais"""
        if self.todas_as_cameras.get() == 1:
            self.execute_all_action(self.handlecam.coletar_seriais)
        else:
            self.execute_camera_action(self.handlecam.coletar_seriais)

    def configurar_auto_maintain(self):
        """Configura o reset semanal das câmeras."""
        if self.todas_as_cameras.get() == 1:
            self.execute_all_action(self.handlecam.configura_automaintain)
        else:
            self.execute_camera_action(self.handlecam.configura_automaintain)

    def consulta_autoregister(self):
        """Consulta as configurações de Auto Register das câmeras."""
        if self.todas_as_cameras.get() == 1:
            self.execute_all_action(self.handlecam.check_auto_register)
        else:
            self.execute_camera_action(self.handlecam.check_auto_register)

    def configurar_autoregister(self):
        """Configura o Auto Register nas câmeras."""
        self.execute_camera_action(self.handlecam.ativar_autoregister)

    def atualiza_firme(self):
        """Consulta os firmwares das câmeras."""
        if self.todas_as_cameras.get() == 1:
            self.execute_all_action(self.handlecam.check_firmeware)
        else:
            self.execute_camera_action(self.handlecam.check_firmeware)

    def configurar_fontes(self):
        """Configura o tamanho automático das fontes nas câmeras."""
        if self.todas_as_cameras.get() == 1:
            self.execute_all_action(self.handlecam.configurar_font_size)
        else:
            self.execute_camera_action(self.handlecam.configurar_font_size)

    def configurar_reset(self):
        """Reinicia as câmeras."""
        if self.todas_as_cameras.get() == 1:
            self.execute_all_action(self.handlecam.reset_cameras)
        else:
            self.execute_camera_action(self.handlecam.reset_cameras)

    def atualizar_modelos(self):
        """Pega o modelo da câmera"""
        if self.todas_as_cameras.get() == 1:
            self.execute_all_action(self.handlecam.gerar_lista_modelos)
        else:
            self.execute_camera_action(self.handlecam.gerar_lista_modelos)

    def consultar_display(self):
        """Pega o display da câmera"""
        if self.todas_as_cameras.get() == 1:
            self.execute_all_action(self.handlecam.nome_cameras)
        else:
            self.execute_camera_action(self.handlecam.nome_cameras)

    def visualizar_snapshot(self):
        """Exibe um sanpshot"""
        self.executa_visualizar_snapshot()

    def exportar_lista_cameras_offline(self):
        """Pega o display da câmera"""
        if self.todas_as_cameras.get() == 1:
            self.execute_all_action(self.handlecam.get_status_cameras)
        else:
            self.execute_camera_action(self.handlecam.get_status_cameras)

    def roteadores_offline(self):
        """Lista os pontos offline"""
        lista_roteadores = self.site_data.roteadores_offline()
        for indice, roteador in enumerate(lista_roteadores, 0):
            self.table.insert(parent='', index='end', iid=indice, text='',
                              values=(roteador[0], roteador[1], roteador[2]))
        self.btn_exportar_resultado.configure(state='active')

    def execute_camera_action(self, action_function):
        """Executa uma ação específica para todas as câmeras do ponto selecionado."""
        try:
            self.btn_parar.config(state='active')
            self.clear_table()
            ponto = self.combo_pontos.get()
            camera_selecionada = self.combo_cameras.get()

            if camera_selecionada == "Todas as Câmeras":
                cameras = Database().selecionar_ponto(ponto)
                for indice, camera in enumerate(cameras, 0):
                    if self.stop:
                        self.stop = False
                        self.btn_parar.config(state='disabled')
                        break
                    response = action_function(camera[4], camera[8], camera[0])
                    if response:
                        self.table.insert(parent='', index='end', iid=indice, text='',
                                          values=(camera[1], camera[5], response))
                self.btn_parar.config(state='disabled')
                self.btn_exportar_resultado.config(state='active')
            else:
                camera = Database().selecionar_camera(camera_selecionada)
                response = action_function(camera[0][4], camera[0][8], camera[0][0])
                if response:
                    self.btn_parar.config(state='disabled')
                    self.btn_exportar_resultado.config(state='active')
                    self.table.insert(parent='', index='end', iid=0, text='',
                                      values=(camera[0][1], camera[0][5], response))
        except IndexError as e:
            messagebox.showinfo(
                "Informação", f"Favor selecionar uma camera para realizar essa ação {e.__str__()}"
            )

    def execute_all_action(self, action_function):
        self.clear_table()
        self.btn_parar.config(state='active')
        self.clear_table()
        cameras = Database().selecionar_todas_cameras()
        for indice, camera in enumerate(cameras, 0):
            if self.stop:
                self.stop = False
                self.btn_parar.config(state='disabled')
                break
            response = action_function(camera[4], camera[8], camera[0])
            if response:
                self.table.insert(parent='', index='end', iid=indice, text='', values=(camera[1], camera[5], response))
        messagebox.showinfo(
            "Atualização Finalizada", "As atualizações foram realizadas."
        )
        self.btn_parar.config(state='disabled')
        self.btn_exportar_resultado.config(state='active')

    def clear_table(self):
        if len(self.table.get_children()) > 0:
            for row in self.table.get_children():
                self.table.delete(row)

    # ====================== THREADS ======================

    @staticmethod
    def start_thread(target_function):
        """Inicia uma thread para executar a função fornecida."""
        threading.Thread(target=target_function).start()

    def thread_atualizar_seriais(self):
        self.start_thread(self.atualizar_seriais)

    def thread_configurar_auto_maintain(self):
        self.start_thread(self.configurar_auto_maintain)

    def thread_consulta_autoregister(self):
        self.start_thread(self.consulta_autoregister)

    def thread_configurar_autoregister(self):
        self.start_thread(self.configurar_autoregister)

    def thread_atualizar_firmwares(self):
        self.start_thread(self.atualiza_firme)

    def thread_configurar_fontes(self):
        self.start_thread(self.configurar_fontes)

    def thread_configurar_reset(self):
        self.start_thread(self.configurar_reset)

    def thread_atualizar_modelos(self):
        self.start_thread(self.atualizar_modelos)

    def thread_consultar_display(self):
        self.start_thread(self.consultar_display)

    def thread_exportar_lista(self):
        self.start_thread(self.exporta_lista)

    def thread_visualizar_snapshot(self):
        self.start_thread(self.visualizar_snapshot)

    def thread_roteador_offline(self):
        self.start_thread(self.roteadores_offline())

    def thread_lista_cameras_offline(self):
        self.start_thread(self.exportar_lista_cameras_offline)

    def thread_gera_lista_tabela(self):
        self.start_thread(self.exportar_resultado)


if __name__ == "__main__":
    PerkonsInfoCam()
