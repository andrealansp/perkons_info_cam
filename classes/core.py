import subprocess
import platform
import os
import random
import re
import sys
import time
from abc import ABC, abstractmethod
from tkinter import messagebox

import requests
from requests.auth import HTTPDigestAuth
from requests.exceptions import Timeout, RequestException, ConnectionError
from typing import List, Tuple, Dict, Optional

from db import Database


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class CameraInterface(ABC):
    """Interface for interacting with camera devices."""

    @abstractmethod
    def check_auto_register(self, ip: str, porta: str, id: int) -> str:
        pass

    @abstractmethod
    def coletar_seriais(self, ip: str, porta: str, id: int) -> Optional[str]:
        pass

    @abstractmethod
    def gerar_lista_modelos(self, ip: str, porta: str, id: int) -> Optional[str]:
        pass

    @abstractmethod
    def check_firmeware(self, ip: str, porta: str, id: int) -> Optional[str]:
        pass

    @abstractmethod
    def listar_enconding_strateg(self, ip: str, porta: str, id: int) -> Optional[str]:
        pass

    @abstractmethod
    def configura_automaintain(self, ip: str, porta: str, id: int) -> Optional[str]:
        pass

    @abstractmethod
    def configurar_font_size(self, ip: str, porta: str, id: int) -> Optional[List[str]]:
        pass

    @abstractmethod
    def desativar_autoregister(self, ip: str, porta: str, id: int) -> Optional[List[int]]:
        pass

    @abstractmethod
    def alterar_ip_autoregister(self, ip: str, porta: str, id: int) -> Optional[List[int]]:
        pass

    @abstractmethod
    def ativar_autoregister(self, ip: str, porta: str, id: int) -> Optional[List[int]]:
        pass

    @abstractmethod
    def reset_cameras(self, ip: str, porta: str, id: int) -> Optional[List[int]]:
        pass

    @abstractmethod
    def nome_cameras(self, ip: str, porta: str, id: int) -> Optional[List[str]]:
        pass

    @abstractmethod
    def get_snapshot(self, endereco: str, nome_arquivo: str, params: Optional[Dict] = None) -> Optional[str]:
        pass

    @abstractmethod
    def get_status_cameras(self, ip: str, porta: str, id: int) -> Optional[str]:
        pass


class HandleInfoCamera(CameraInterface):
    """Implementation for interacting with Hikvision cameras."""

    def __init__(self, database: Database, auth: HTTPDigestAuth = HTTPDigestAuth("admin", "perkons6340"), timeout: int = 2):
        self.database = database
        self.auth = auth
        self.timeout = timeout

    def _make_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        try:
            response = requests.get(url, auth=self.auth, timeout=self.timeout, params=params)
            response.raise_for_status()
            return response
        except Timeout:
            raise Timeout(f"Timeout ao conectar em: {url.split('/')[2]}")
        except ConnectionError:
            raise ConnectionError(f"Erro de conexão com {url.split('/')[2]}")
        except RequestException as e:
            raise RequestException(f"Erro na requisição para {url.split('/')[2]}: {e}")

    def check_auto_register(self, ip: str, porta: str, id: int) -> str:
        try:
            urlport = f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=getConfig&name=DVRIP"
            response = self._make_request(urlport)
            returneddata = response.text.split("\r\n")
            device_id = returneddata[5].split("=")[1]
            status = returneddata[6].split("=")[1]
            ar_ip = returneddata[7].split("=")[1]
            ar_porta = returneddata[8].split("=")[1]
            return f"""ID {id} - IP: {ar_ip} - Porta: {ar_porta} - Status: {status} - DeviceId: {device_id}"""
        except (Timeout, RequestException, ConnectionError) as e:
            return f"Câmera {porta} Está offline: {e}"

    def coletar_seriais(self, ip: str, porta: str, id: int) -> Optional[str]:
        try:
            urlport = f"http://{ip}:{porta}/cgi-bin/magicBox.cgi?action=getSerialNo"
            response = self._make_request(urlport)
            returneddata = response.text.split("\r\n")
            resposta = returneddata[0]
            re_sub_serial = re.sub(r"(sn=)(\w{15})", r"\2", resposta)
            self.database.atualizar_serial_camera(serial=re_sub_serial, id=id)
            return re_sub_serial
        except (Timeout, RequestException, ConnectionError) as e:
            return f"Câmera {porta} está offline: {e}"
        return None

    def gerar_lista_modelos(self, ip: str, porta: str, id: int) -> Optional[str]:
        try:
            urlport = f"http://{ip}:{porta}/cgi-bin/magicBox.cgi?action=getDeviceType"
            response = self._make_request(urlport, timeout=3)  # Increased timeout for this
            returneddata = response.text
            modelo = re.sub(
                r'(type=)(\w{3}\d{3}.\w{2}\d\w.\w{2}\d|\w{3}.\w{3}\d{4}\w.\w{2})(?:\\[rn"\"]|[\r\n]+)+',
                r"\2",
                returneddata,
            )
            self.database.atualizar_modelo_camera(modelo=modelo, id=id)
            return modelo
        except (Timeout, RequestException, ConnectionError) as e:
            return f"Câmera {porta} Está offline: {e}"
        return None

    def check_firmeware(self, ip: str, porta: str, id: int) -> Optional[str]:
        try:
            urlport = f"http://{ip}:{porta}/cgi-bin/magicBox.cgi?action=getSoftwareVersion"
            response = self._make_request(urlport)
            returneddata = response.text.split("\r\n")
            retorno_firmware = re.sub(
                r"(\w{7}.)(\d.\d{3}.[WG0-9]{7}.\d{1,2}.\w,)(\w{5}.)(\d{4}.\d{2}.\d{2})",
                r"Versão: \2 - Build: \4",
                returneddata[0],
            )
            self.database.atualizar_firmeware_camera(firmware=retorno_firmware, id=id)
            return retorno_firmware
        except (Timeout, RequestException, ConnectionError) as e:
            return f"Câmera {porta} Está offline: {e}"
        return None

    def listar_enconding_strateg(self, ip: str, porta: str, id: int) -> Optional[str]:
        try:
            urlport = f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=getConfig&name=SmartEncode&name=AICoding"
            response = self._make_request(urlport)
            returneddata = response.text
            time.sleep(0.5)
            resposta_aicode = re.sub(
                r"(\w{5}).(\w{8,11})\D.\D.(\w{6}.)(\w{3,5})", r"\2 -\4", returneddata
            )
            return resposta_aicode
        except (Timeout, RequestException, ConnectionError) as e:
            return f"A Câmera {id}:{porta} está offline: {e}"
        return None

    def configura_automaintain(self, ip: str, porta: str, id: int) -> Optional[str]:
        opcoes = {
            str(i): {
                "action": "setConfig",
                "AutoMaintain.AutoRebootDay": i,
                "AutoMaintain.AutoRebootHour": i - 1 if i > 0 else 0,
                "AutoMaintain.AutoRebootMinute": 0,
            }
            for i in range(1, 7)
        }
        try:
            urlport = f"http://{ip}:{porta}/cgi-bin/configManager.cgi"
            params = opcoes[str(random.randint(1, 6))]
            response = self._make_request(urlport, params=params)
            time.sleep(0.5)
            if response.status_code == 200:
                return "Alterada a configuração com sucesso !"
            return None
        except (Timeout, RequestException, ConnectionError) as e:
            return f"Câmera {porta} Está offline: {e}"
        return None

    def configurar_font_size(self, ip: str, porta: str, id: int) -> Optional[List[str]]:
        respostas = []
        try:
            urls = [
                f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&VideoWidget[0].FontSize=0",
                f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&VideoWidget[0].FontExtra1=0",
            ]
            for url in urls:
                response = self._make_request(url)
                returneddata = response.text.split("\r\n")
                time.sleep(0.2)
                respostas.append(returneddata[0])
            return respostas
        except (Timeout, RequestException, ConnectionError) as e:
            return f"Câmera {porta} Está offline: {e}"
        return None

    def desativar_autoregister(self, ip: str, porta: str, id: int) -> Optional[List[int]]:
        try:
            url = f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&DVRIP.RegisterServer.Enable=false"
            response = self._make_request(url)
            return [response.status_code]
        except (Timeout, RequestException, ConnectionError) as e:
            return [f"Câmera {porta} Está offline: {e}"]
        return None

    def alterar_ip_autoregister(self, ip: str, porta: str, id: int) -> Optional[List[int]]:
        try:
            url = (
                f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&DVRIP.RegisterServer"
                f".Servers[0].Address=177.154.22.66"
            )
            response = self._make_request(url)
            return [response.status_code]
        except (Timeout, RequestException, ConnectionError) as e:
            return [f"Câmera {porta} Está offline: {e}"]
        return None

    def ativar_autoregister(self, ip: str, porta: str, id: int) -> Optional[List[int]]:
        try:
            url = f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=setConfig&DVRIP.RegisterServer.Enable=true"
            response = self._make_request(url)
            return [response.status_code]
        except (Timeout, RequestException, ConnectionError) as e:
            return [f"Câmera {porta} Está offline: {e}"]
        return None

    def reset_cameras(self, ip: str, porta: str, id: int) -> Optional[List[int]]:
        try:
            url = f"http://{ip}:{porta}/cgi-bin/magicBox.cgi?action=shutdown"
            response = self._make_request(url)
            return [response.status_code]
        except (Timeout, RequestException, ConnectionError) as e:
            return [f"Câmera {porta} Está offline: {e}"]
        return None

    def nome_cameras(self, ip: str, porta: str, id: int) -> Optional[List[str]]:
        try:
            url = f"http://{ip}:{porta}/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle"
            response = self._make_request(url)
            return [
                response.text.split("=")[1]
                .replace("\r\n", " ")
                .replace("table.ChannelTitle[0].SerialNo", " ")
            ]
        except (Timeout, RequestException, ConnectionError) as e:
            return [f"Câmera {porta} Está offline: {e}"]
        return None

    def get_snapshot(self, endereco: str, nome_arquivo="snapshot.jpg", params: Optional[Dict] = None) -> Optional[str]:
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
            url = f"http://{endereco}/cgi-bin/snapshot.cgi"
            response = self._make_request(url, params=params)

            # O conteúdo da resposta é o binário da imagem JPEG
            imagem_binaria = response.content

            # Abre um arquivo no modo de escrita binária ('wb') e escreve o conteúdo
            with open(nome_arquivo, 'wb') as arquivo:
                arquivo.write(imagem_binaria)

            return nome_arquivo

        except (Timeout, RequestException, ConnectionError) as e:
            print(f"Erro ao obter o snapshot de {endereco}: {e}")
            return None

    def get_status_cameras(self, ip: str, porta: str, id: int) -> Optional[str]:
        try:
            url = f"http://{ip}:{porta}/cgi-bin/magicBox.cgi?action=getSystemInfo"
            response = self._make_request(url)
            if response.status_code == 200:
                return None

        except (Timeout, RequestException, ConnectionError) as e:
            return f"Câmera {porta} Está offline: {e}"
        return None

class SiteData:
    """Class to handle site-related data operations."""

    def __init__(self, database: Database):
        self.database = database
        self.pontos: List[str] = []

    def get_list_sites_names(self) -> Optional[List[str]]:
        try:
            retorno_select = self.database.selecionar_nomes_sites()
            self.pontos = [ponto[0] for ponto in retorno_select]
            return self.pontos
        except Exception as e:
            messagebox.showinfo(
                "Sem conexão", f"Favor realizar a conexão com a VPN Perkons! {e.__str__()} "
            )
            return None

    def roteadores_offline(self):
        roteadores = self.database.selecionar_ip_roteadores()
        roteadores_sem_resposta = []
        try:
            for roteador in roteadores:
                if not NetworkUtils.verificar_ping(str(roteador[1])):
                    roteadores_sem_resposta.append((roteador[0], roteador[2], f"Ponto {roteador[0]} off-line!"))
            return roteadores_sem_resposta
        except Exception as e:
            print(f"Erro: {e}")

    def get_list_sites(self) -> List[Tuple[str, str, str, str]]:
        cameras: List[Tuple[str, str, str, str]] = []
        retorno_select = self.database.selecionar_todas_cameras()
        for site in retorno_select:
            cameras.append((site[0], site[1], site[3], site[4]))
        return cameras


class NetworkUtils:
    """Utility class for network-related operations."""

    @staticmethod
    def verificar_ping(ip_address: str) -> bool:
        """
        Verifica se um endereço IP está respondendo ao ping.

        Args:
            ip_address (str): O endereço IP a ser verificado.

        Returns:
            bool: True se o IP estiver pingando, False caso contrário.
        """
        param = "-n" if platform.system().lower() == "windows" else "-c"
        comando = ["ping", param, "1", ip_address]

        try:
            # Executa o comando de ping e redireciona a saída para /dev/null (Linux/macOS)
            # ou NUL (Windows) para evitar a exibição na tela.
            if platform.system().lower() == "windows":
                subprocess.check_call(
                    comando,
                    timeout=2,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.check_call(
                    comando,
                    timeout=2,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return True
        except subprocess.TimeoutExpired:
            return False
        except subprocess.CalledProcessError:
            return False
        except OSError as e:
            print(f"Erro ao executar o comando ping: {e}")
            return