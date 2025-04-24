from ast import Return
import json
import os
import random
import re
import sys
import time
from tkinter import messagebox

import requests
from requests.auth import HTTPDigestAuth
from requests.exceptions import Timeout

from db import Database


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


pontos = []
database = Database()


def check_auto_register(ip: str, porta: str, id: int):
    try:
        urlport = (
            f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=getConfig&name=DVRIP"
        )
        s = requests.get(
            urlport, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1
        )
        returneddata = s.text.split("\r\n")
        time.sleep(0.2)
        deviceId = returneddata[5].split("=")[1]
        status = returneddata[6].split("=")[1]
        ar_ip = returneddata[7].split("=")[1]
        ar_porta = returneddata[8].split("=")[1]

        return f"""ID {id} - IP: {ar_ip} - Porta: {ar_porta} - Status: {status} - DeviceId: {deviceId}"""

    except Timeout:
        return f"Câmera {porta} Está offline"


def coletar_seriais(ip: str, porta: str, id):
    try:
        urlport = f"http://{ip}:{porta}/cgi-bin/magicBox.cgi?action=getSerialNo"
        s = requests.get(
            urlport, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1
        )
        returneddata = s.text.split("\r\n")
        resposta = returneddata[0]
        re_sub_serial = re.sub(r"(sn=)(\w{15})", r"\2", resposta)
        database.atualizar_serial_camera(serial=re_sub_serial, id=id)
        return re_sub_serial
    except Timeout:
        return f"Câmera {porta} está offline"


def gerar_lista_modelos(ip: str, porta: str, id: int):
    try:
        urlport = f"http://{ip}:{porta}/cgi-bin/magicBox.cgi?action=getDeviceType"
        s = requests.get(
            urlport, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=2
        )
        returneddata = s.text
        time.sleep(0.2)
        modelo = re.sub(
            r'(type=)(\w{3}\d{3}.\w{2}\d\w.\w{2}\d|\w{3}.\w{3}\d{4}\w.\w{2})(?:\\[rn"\"]|[\r\n]+)+',
            r"\2",
            returneddata,
        )
        database.atualizar_modelo_camera(modelo=modelo, id=id)
        return modelo
    except Timeout:
        return f"Câmera {porta} Está offline"


def check_firmeware(ip: str, porta: str, id: int):
    try:
        urlport = f"http://{ip}:{porta}/cgi-bin/magicBox.cgi?action=getSoftwareVersion"
        s = requests.get(
            urlport, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1
        )
        returneddata = s.text.split("\r\n")
        time.sleep(0.2)
        retorno_firmware = re.sub(
            r"(\w{7}.)(\d.\d{3}.[WG0-9]{7}.\d{1,2}.\w,)(\w{5}.)(\d{4}.\d{2}.\d{2})",
            r"Versão: \2 - Build: \4",
            returneddata[0],
        )
        database.atualizar_firmeware_camera(firmware=retorno_firmware, id=id)
        return retorno_firmware
    except Timeout:
        return f"Câmera {porta} Está offline"
    except requests.exceptions.RetryError:
        return f"Câmera {porta} Está offline"
    except requests.exceptions.ConnectionError:
        return f"Câmera {porta} Está offline"


def listar_enconding_strateg(ip: str, porta: str, id: int):
    try:
        urlport = f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=getConfig&name=SmartEncode&name=AICoding"
        s = requests.get(
            urlport, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1
        )
        returneddata = s.text
        time.sleep(0.5)
        resposta_aicode = re.sub(
            r"(\w{5}).(\w{8,11})\D.\D.(\w{6}.)(\w{3,5})", r"\2 -\4", returneddata
        )
        return resposta_aicode
    except Timeout:
        return f"A Câmera {id}:{porta} está offline!"


def configura_automaintain(ip: str, porta: str, id: int):
    opcoes = {
        "1": {
            "action": "setConfig",
            "AutoMaintain.AutoRebootDay": 1,
            "AutoMaintain.AutoRebootHour": 0,
            "AutoMaintain.AutoRebootMinute": 0,
        },
        "2": {
            "action": "setConfig",
            "AutoMaintain.AutoRebootDay": 2,
            "AutoMaintain.AutoRebootHour": 1,
            "AutoMaintain.AutoRebootMinute": 0,
        },
        "3": {
            "action": "setConfig",
            "AutoMaintain.AutoRebootDay": 3,
            "AutoMaintain.AutoRebootHour": 2,
            "AutoMaintain.AutoRebootMinute": 0,
        },
        "4": {
            "action": "setConfig",
            "AutoMaintain.AutoRebootDay": 4,
            "AutoMaintain.AutoRebootHour": 3,
            "AutoMaintain.AutoRebootMinute": 0,
        },
        "5": {
            "action": "setConfig",
            "AutoMaintain.AutoRebootDay": 5,
            "AutoMaintain.AutoRebootHour": 4,
            "AutoMaintain.AutoRebootMinute": 0,
        },
        "6": {
            "action": "setConfig",
            "AutoMaintain.AutoRebootDay": 6,
            "AutoMaintain.AutoRebootHour": 5,
            "AutoMaintain.AutoRebootMinute": 0,
        },
    }

    try:
        urlport = f"http://{ip}:{porta}/cgi-bin/configManager.cgi"
        s = requests.get(
            urlport,
            params=opcoes[str(random.randint(1, 6))],
            auth=HTTPDigestAuth("admin", "perkons6340"),
            timeout=1,
        )
        returneddata = s.status_code
        time.sleep(0.5)
        if returneddata == 200:
            return "Alterada a configuração com sucesso !"
        return None
    except Timeout:
        return f"Câmera {porta} Está offline"


def configurar_font_size(ip: str, porta: str, _):
    respostas = []
    try:
        urls = [
            f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&VideoWidget[0].FontSize=0",
            f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&VideoWidget[0].FontExtra1=0",
        ]
        for url in urls:
            s = requests.get(
                url, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1
            )
            returneddata = s.text.split("\r\n")
            time.sleep(0.2)
            respostas.append(returneddata[0])
        return respostas
    except Timeout:
        return f"Câmera {porta} Está offline"


def configurar_reset():
    cameras = database.selecionar_todas_cameras()
    for row in cameras.fetchall():
        print(
            row[0].value,
            "-",
            configura_automaintain(row[4].value, row[8].value, random.randint(1, 6)),
        )
        print(
            row[0].value,
            "-",
            configura_automaintain(row[1].value, row[3].value, random.randint(1, 6)),
        )


def desativar_autoregister(ip: str, porta: str, _):
    resposta = []
    try:
        url = f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&DVRIP.RegisterServer.Enable=false"
        s = requests.get(url, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1)
        resposta.append(s.status_code)
        return resposta
    except Timeout:
        return f"Câmera {porta} Está offline"


def alterar_ip_autoregister(ip: str, porta: str, _):
    resposta = []
    try:
        url = (
            f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&DVRIP.RegisterServer"
            f".Servers[0].Address=177.154.22.66"
        )
        s = requests.get(url, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1)
        resposta.append(s.status_code)
        return resposta
    except Timeout:
        return f"Câmera {porta} Está offline"


def ativar_autoregister(ip: str, porta: str, _):
    resposta = []
    try:
        url = f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&DVRIP.RegisterServer.Enable=true"
        s = requests.get(url, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1)
        resposta.append(s.status_code)
        return resposta
    except Timeout:
        return f"Câmera {porta} Está offline"


def reset_cameras(ip: str, porta: str, _):
    resposta = []
    try:
        url = f"http://{ip}:{porta}/cgi-bin/magicBox.cgi?action=shutdown"
        s = requests.get(url, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1)
        resposta.append(s.status_code)
        return resposta
    except Timeout:
        return f"Câmera {porta} Está offline"


def nome_cameras(ip: str, porta: str, _):
    resposta = []
    try:
        url = f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle"
        s = requests.get(url, auth=HTTPDigestAuth("admin", "perkons6340"), timeout=1)
        resposta.append(
            s.text.split("=")[1]
            .replace("\r\n", " ")
            .replace("table.ChannelTitle[0].SerialNo", " ")
        )
        return resposta
    except Timeout:
        return f"Câmera {porta} Está offline"


def get_list_sites_names():
    try:
        retorno_select = database.selecionar_nomes_sites()
        for ponto in retorno_select:
            pontos.append(ponto[0])
        return pontos
    except Exception as e:
        messagebox.showinfo(
            "Sem conexão", f"Favor realizar a conexão com a VPN Perkons! {e.__str__()} "
        )
        return None


def get_list_sites():
    cameras: list = []
    retorno_select = database.selecionar_todas_cameras()
    for site in retorno_select:
        cameras.append((site[0], site[1], site[3], site[4]))
    return cameras


def get_snapshot(endereco, nome_arquivo="snapshot.jpg", params=None):
    """
    Obtém o binário de uma imagem de um URL e salva num arquivo local.

    Args:
        endereco (str): texto concatenado do ip:porta.
        nome_arquivo (str, opcional): O nome do arquivo para salvar a imagem localmente.
                                     Padrão é "snapshot.jpg".
        params (dict, opcional): Um dicionário de parâmetros de consulta a serem enviados com a solicitação.
                                 Padrão é None.
    """
    try:
        response = requests.get(f"http://{endereco}/cgi-bin/snapshot.cgi", params=params, auth=HTTPDigestAuth("admin", "perkons6340"))
        response.raise_for_status()  # Levanta uma exceção para códigos de status de erro

        # O conteúdo da resposta é o binário da imagem JPEG
        imagem_binaria = response.content

        # Abre um arquivo no modo de escrita binária ('wb') e escreve o conteúdo
        with open(nome_arquivo, 'wb') as arquivo:
            arquivo.write(imagem_binaria)

        return nome_arquivo

    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter o snapshot: {e}")
        return None


if __name__ == '__main__':
    # Exemplo de uso com o URL e parâmetro do canal
    endereco = "200.6.137.102:8091"
    url_snapshot = f"http://{endereco}/cgi-bin/snapshot.cgi"  # Substitua pelo endereço real
    parametro_canal = {'channel': 1}
    nome_do_arquivo = f"snapshot_canal_{parametro_canal['channel']}_{endereco.split(":")[0]}_{endereco.split(":")[1]}.jpg"
    get_snapshot(url_snapshot,nome_do_arquivo,parametro_canal)
