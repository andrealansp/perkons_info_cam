from pprint import pprint
import time
import traceback
from venv import logger
import psycopg


class Database:
    def __init__(self):
        self.__con = {
            "dbname": "bd_regional",
            "user": "perkons",
            "password": "perkons6340",
            "host": "10.1.5.158",  # Change if your database is hosted elsewhere
            "port": 5432,  # Default PostgreSQL port
        }

    @property
    def con(self):
        return self.__con

    def criar_tabela(self):
        try:
            with psycopg.connect(**self.con) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """CREATE TABLE IF NOT EXISTS cameras (
        id SERIAL PRIMARY KEY,
        ponto VARCHAR(6) NOT NULL,
        regiao VARCHAR(50) NOT NULL,
        nome_ponto VARCHAR(100) NOT NULL,
        ip INET NOT NULL,
        nome_camera VARCHAR(150) UNIQUE NOT NULL,
        firmware VARCHAR(50),
        serial VARCHAR(50),
        porta VARCHAR(6) NOT NULL,
        modelo VARCHAR(150),
        longitude VARCHAR(10),
        latitude VARCHAR(10)
    );"""
                    )
        except Exception as e:
            print("Error creating table", e)

    def inserir_camera(self, camera):
        insert_sql = """ INSERT INTO public.cameras(
	ponto, regiao, nome_ponto, ip, nome_camera, firmware, serial, porta, modelo, longitude, latitude)
	VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); """

        try:
            with psycopg.connect(**self.con) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        insert_sql,
                        (
                            camera.get("ponto", "Sem coleta"),
                            camera.get("regiao", "Sem coleta"),
                            camera.get("nome_ponto", "Sem coleta"),
                            camera.get("ip", "Sem coleta"),
                            camera.get("nome_camera", "Sem coleta"),
                            camera.get("firmware", "Sem coleta"),
                            camera.get("serial", "Sem coleta"),
                            camera.get("porta", "Sem coleta"),
                            camera.get("modelo", "Sem coleta"),
                            camera.get("longitude", "Sem coleta"),
                            camera.get("latitude", "Sem coleta"),
                        ),
                    )
                    conn.commit()
                    print(f"Câmera adicionada com sucesso!")
                    time.sleep(1)
        except psycopg.Error as e:
            logger.error("Error inserting user:", e, traceback.format_exc())
        except Exception as e:
            logger.error("Unexpected error:", e, traceback.format_exc())

    def selecionar_todas_cameras(self):

        with psycopg.connect(**self.con) as con:
            with con.cursor() as cur:

                cur.execute("""select * from cameras ORDER BY ponto""")
                return cur.fetchall()

    def selecionar_nomes_sites(self):

        with psycopg.connect(**self.con) as con:
            with con.cursor() as cur:

                cur.execute("""SELECT DISTINCT ponto FROM cameras ORDER BY ponto """)
                return cur.fetchall()

    def selecionar_ponto(self, ponto):

        with psycopg.connect(**self.con) as con:
            with con.cursor() as cur:

                cur.execute("""SELECT * FROM cameras WHERE ponto = %s """, (ponto,))
                return cur.fetchall()

    def selecionar_camera(self, nome_camera):

        with psycopg.connect(**self.con) as con:
            with con.cursor() as cur:

                cur.execute(
                    """SELECT * FROM cameras WHERE nome_camera = %s """, (nome_camera,)
                )
                return cur.fetchall()

    def atualizar_serial_camera(self, serial, id):

        try:
            with psycopg.connect(**self.con) as conn:
                with conn.cursor() as cur:

                    cur.execute(
                        """UPDATE public.cameras SET serial=%s, atualizado=now() WHERE id = %s;""",
                        (serial, id),
                    )
                    conn.commit()
                    logger.info("Serial Atualizado!")
        except psycopg.Error as e:
            logger.error("Error inserting user:", e, traceback.format_exc())
        except Exception as e:
            logger.error("Unexpected error:", e, traceback.format_exc())

    def atualizar_firmeware_camera(self, firmware, id):
        try:
            with psycopg.connect(**self.con) as conn:
                with conn.cursor() as cur:

                    cur.execute(
                        """UPDATE public.cameras SET firmware=%s, atualizado=now() WHERE id = %s;""",
                        (firmware, id),
                    )
                    conn.commit()
                    logger.info("Serial Atualizado!")
        except psycopg.Error as e:
            logger.error("Error inserting user:", e, traceback.format_exc())
        except Exception as e:
            logger.error("Unexpected error:", e, traceback.format_exc())

    def atualizar_modelo_camera(self, modelo, id):
        try:
            with psycopg.connect(**self.con) as conn:
                with conn.cursor() as cur:

                    cur.execute(
                        """UPDATE public.cameras SET modelo=%s, atualizado=now() WHERE id = %s;""",
                        (modelo, id),
                    )
                    conn.commit()
                    logger.info("Serial Atualizado!")
        except psycopg.Error as e:
            logger.error("Error inserting user:", e, traceback.format_exc())
        except Exception as e:
            logger.error("Unexpected error:", e, traceback.format_exc())


if __name__ == "__main__":
    banco_dados = Database()
    # banco_dados.criar_tabela()
    # ponto = {
    #     "ponto": "P0001",
    #     "regiao": "Metropolitana",
    #     "nome_ponto": "P0001-PCL-PK-GRP",
    #     "ip": "45.182.66.1",
    #     "nome_camera": "GRP-P0001-LPR2-SAIDA-ES060-KM29N",
    #     "porta": "9051",
    # }
    # banco_dados.inserir_camera(ponto)
    # # banco_dados.pegar_todas_cameras()
    cameras = banco_dados.selecionar_ponto("P0002")
    pprint(cameras)
