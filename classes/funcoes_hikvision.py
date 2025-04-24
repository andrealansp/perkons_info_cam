import requests
from requests.auth import HTTPDigestAuth
import xmltodict
import cv2


class Hikvision:
    def __init__(self, ip: str, porta: str, usuario: str, senha: str):
        self.ip = ip
        self.porta = porta
        self.usuario = usuario
        self.senha = senha
        self.retorno: dict[str, str]= None

    def pegar_informacoes(self):
        
        try:
            response =  requests.get(f"http://{self.ip}:{self.porta}/ISAPI/System/deviceInfo",
                                     auth=HTTPDigestAuth(self.usuario, self.senha))
            if response.status_code == 200:
                data_dict = xmltodict.parse(response.text)
                self.retorno   = data_dict
            return self.retorno

        except requests.exceptions.RequestException as e:
            print(e)

    def salvar_snapshot(self):
         try:
             response = requests.get(f"http://{self.ip}:{self.porta}/ISAPI/Streaming/channels/101/picture",
                                     auth=HTTPDigestAuth(self.usuario, self.senha), stream=True)

             if response.status_code == 200:
                 with open(f"{self.ip}_{self.porta}.jpg", "wb") as f:
                     f.write(response.content)
                 print("Imagem salva com sucesso!")

         except requests.exceptions.RequestException as e:
             print(e)

    def visualizar_video(self):
        try:
            rtsp_url = f"rtsp://{self.usuario}:{self.senha}@8129.pkt.perkons.com:30011/cam/realmonitor?channel=1&subtype=0"
            print(rtsp_url)

            cap = cv2.VideoCapture(rtsp_url)

            if not cap.isOpened():
                print("Erro ao obter o video")
            else:
                print("Stream Iniciado. Pressione q para finalizar")

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Erro ao obter o video")
                    break

                cv2.imshow(f"{self.ip}:{self.porta}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                cap.release()
                cv2.destroyAllWindows()

        except requests.exceptions.RequestException as e:
            print(e)

if __name__ == '__main__':
    hik = Hikvision("10.15.164.98","8080", "admin", "perkons6340")
    hik.visualizar_video()