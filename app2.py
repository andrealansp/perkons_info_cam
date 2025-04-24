import subprocess
import numpy as np
import cv2
import time


def capture_rtsp_with_ffmpeg(rtsp_url):
    """
    Captura um stream RTSP usando FFmpeg como intermediário.

    Args:
        rtsp_url (str): URL do stream RTSP
    """
    # Comando FFmpeg para ler o stream RTSP e enviá-lo para stdout em formato raw
    command = [
        "ffmpeg",
        "-i",
        rtsp_url,
        "-rtsp_transport",
        "tcp",  # Use TCP ao invés de UDP (mais estável)
        "-f",
        "image2pipe",
        "-pix_fmt",
        "bgr24",  # Formato de pixel compatível com OpenCV
        "-vcodec",
        "rawvideo",
        "-",  # Saída para stdout
    ]

    # Inicia o processo FFmpeg
    try:
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)

        # Primeiro frame para determinar tamanho
        raw_image = pipe.stdout.read(1920 * 1080 * 3)  # Largura x Altura x 3 canais BGR

        if not raw_image:
            print("Erro: Não foi possível ler o stream")
            return

        # Redimensione conforme necessário se souber as dimensões exatas
        image = np.frombuffer(raw_image, dtype="uint8").reshape((1080, 1920, 3))

        # Agora que temos o tamanho, podemos continuar capturando
        while True:
            # Mostra o frame atual
            cv2.imshow("RTSP Stream via FFmpeg", image)

            # Lê o próximo frame
            raw_image = pipe.stdout.read(1920 * 1080 * 3)
            if not raw_image:
                break

            image = np.frombuffer(raw_image, dtype="uint8").reshape((1080, 1920, 3))

            # Pressione 'q' para sair
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("Captura interrompida pelo usuário")
    finally:
        pipe.kill()
        cv2.destroyAllWindows()


# Solução 2: Usando VLC Python bindings para capturar o stream
def capture_rtsp_with_vlc(rtsp_url):
    """
    Captura um stream RTSP usando VLC (requer python-vlc instalado).

    Args:
        rtsp_url (str): URL do stream RTSP
    """
    import vlc
    import time
    import numpy as np

    # Cria uma instância do VLC
    instance = vlc.Instance()

    # Cria um player de mídia
    player = instance.media_player_new()

    # Cria um objeto de mídia com a URL RTSP
    media = instance.media_new(rtsp_url)

    # Configura o player para usar a mídia
    player.set_media(media)

    # Configura a saída como um buffer de memória (para capturar frames)
    player.video_set_format(
        "RV32", 1920, 1080, 1920 * 4
    )  # Ajuste o tamanho conforme necessário

    # Inicializa um array para armazenar os frames
    frame_buffer = np.zeros((1080, 1920, 4), dtype=np.uint8)

    # Define uma função de callback para capturar frames
    @vlc.CallbackDecorators.VideoLockCb
    def _lock(opaque, planes):
        planes[0] = frame_buffer.ctypes.data
        return None

    @vlc.CallbackDecorators.VideoDisplayCb
    def _display(opaque, picture):
        # Converte de RV32 para RGB
        frame = frame_buffer.copy()
        # Mostrar o frame usando OpenCV
        cv2.imshow("RTSP Stream via VLC", frame)
        return None

    # Configura os callbacks
    player.video_set_callbacks(_lock, None, _display, None)

    # Inicia a reprodução
    player.play()

    try:
        while True:
            # Verifica se pressionou 'q' para sair
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            time.sleep(0.01)  # Pequeno delay para não sobrecarregar a CPU
    except KeyboardInterrupt:
        print("Captura interrompida pelo usuário")
    finally:
        player.stop()
        cv2.destroyAllWindows()


# Solução 3: Usando GStreamer com OpenCV
def capture_rtsp_with_gstreamer(rtsp_url):
    """
    Captura um stream RTSP usando GStreamer através do OpenCV.

    Args:
        rtsp_url (str): URL do stream RTSP
    """
    # Criando pipeline GStreamer
    gst_str = (
        f"rtspsrc location={rtsp_url} latency=0 ! "
        "rtph264depay ! h264parse ! avdec_h264 ! "
        "videoconvert ! appsink"
    )

    # Abrindo o stream com OpenCV usando o backend GStreamer
    cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print("Falha ao abrir o stream com GStreamer")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erro ao receber o frame.")
                break

            cv2.imshow("RTSP Stream via GStreamer", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        print("Captura interrompida pelo usuário")
    finally:
        cap.release()
        cv2.destroyAllWindows()


# Solução 4: OpenCV com parâmetros RTSP específicos
def capture_rtsp_with_opencv_params(rtsp_url):
    """
    Captura um stream RTSP com OpenCV usando parâmetros adicionais.

    Args:
        rtsp_url (str): URL do stream RTSP
    """
    # Criando o objeto VideoCapture
    cap = cv2.VideoCapture()

    # Configurando parâmetros RTSP antes de abrir a conexão
    cap.set(cv2.CAP_PROP_PROTOCOL_CACHING, 0)  # Desativa cache
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Tamanho do buffer

    # Força o uso de transporte TCP para RTSP
    os_env = os.environ.copy()
    os_env["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    # Abrindo a conexão
    cap.open(rtsp_url, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("Falha ao abrir o stream com parâmetros OpenCV")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erro ao receber o frame.")
                break

            cv2.imshow("RTSP Stream via OpenCV com parâmetros", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        print("Captura interrompida pelo usuário")
    finally:
        cap.release()
        cv2.destroyAllWindows()


# Tente cada uma das funções acima com sua URL RTSP
if __name__ == "__main__":
    import os

    rtsp_url = "rtsp://admin:perkons6340@8129.pkt.perkons.com:30011/cam/realmonitor?channel=1&subtype=0"

    print("Escolha um método:")
    print("1. FFmpeg")
    print("2. VLC (requer python-vlc)")
    print("3. GStreamer (requer GStreamer instalado)")
    print("4. OpenCV com parâmetros avançados")

    choice = input("Digite o número da opção: ")

    if choice == "1":
        capture_rtsp_with_ffmpeg(rtsp_url)
    elif choice == "2":
        capture_rtsp_with_vlc(rtsp_url)
    elif choice == "3":
        capture_rtsp_with_gstreamer(rtsp_url)
    elif choice == "4":
        capture_rtsp_with_opencv_params(rtsp_url)
    else:
        print("Opção inválida")
