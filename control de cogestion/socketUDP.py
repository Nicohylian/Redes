from threading import Timer
import socket


class SocketUDP:
    """ La clase SocketUDP es un wrapper de la clase socket provista por python.
    Este permite el manejo de múltiples timers que pueden detenerse manualmente
    incluso si la función recvfrom ha recibido algo.
    """

    def __init__(self):
        """ Constructor de la clase SocketUDP. Contiene los siguientes
        parámetros:
         - socket_udp: corresponde a un socket no orientado a conexión de
         python. Este se inicializa como no bloqueante para poder simular el
         manejo de timers.
         - timeout: corresponde al tiempo en segundos que esperará cualquier
         timer antes de lanzar un TimeoutError. Se inicializa con un valor
         negativo (no válido).
         - timer_list: contiene la lista de Timers. Estos timers corresponden
         a objetos Timer provistos por threading de python. Note que estos
         objetos no pueden ser reutilizados. Inicialmente esta lista se
         encuentra vacía.
         - announce_timeout: corresponde a una lista de valores booleanos que
         indica si un timer debe ser anunciado a través de un TimeoutError. El
         anuncio de timeout se realiza una única vez para cada timer, salvo que
         este se resetee.
         - timed_out_timers: lista de ints que contiene los índices de los
         timers en timer_list que ya cumplieron su timeout.

        """
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_udp.setblocking(False)
        self.timeout = -1.0
        self.timer_list = [None]
        self.announce_timeout = [False]
        self.timed_out_timers = []

    def bind(self, address: tuple[str, int]) -> None:
        """ Wrapper de función bind. Funciona igual que en sockets de python.

        :param address: tuple[str, int]
            par (IP, puerto) donde escuchará el socket_udp.
        :return: None
        """
        self.socket_udp.bind(address)

    def settimeout(self, timeout: float) -> None:
        """ Configura el tiempo en segundos que esperará cada timer antes de
        detenerse.

        Al configurarse añade un timer en caso de no haberse configurado uno
        (o más) previamente.

        :param timeout: float
            tiempo en segundos que espera cada timer.
        :return: None
        """
        # guarda el timepo de timeout
        self.timeout = timeout

    def set_timer_list_length(self, number_of_timers: int) -> None:
        """ Añade o remueve elementos de las listas asociadas a los timers.

        :param number_of_timers: int
            número de timers que se desea manejar.
        :return: None
        """
        if number_of_timers == 0:
            return 
        # si faltan timers se añaden
        while len(self.timer_list) < number_of_timers:
            self.timer_list.append(None)
            self.announce_timeout.append(False)
        # si sobran timers se sacan del final de la lista
        while len(self.timer_list) > number_of_timers:
            self.timer_list.pop()
            self.announce_timeout.pop()

    def sendto(self, data: bytes, address: tuple[str, int], timer_index=0) -> None:
        """ Wrapper de la función sendto de python que permite el manejo de
        timers.

        Si se desea que se inicie un timer específico al realizar el envío de
        datos, se debe indicar a través de la variable timer_index.

        Dentro de esta función se crea un nuevo objeto Timer de threading, se
        añade a la lista en la posición timer_index, y se echa a correr luego
        de enviar los datos. Una vez el objeto Timer cumple su tiempo de espera
        llama a la función self._time_up_function con timer_index como parámetro.

        :param data: bytes
            mensaje que se desea enviar.
        :param address: tuple[str, int]
            par (IP, puerto) donde se enviará data.
        :param timer_index: int
            índice del timer asociado al mensaje enviado. Su valor por defecto
            es 0.
        :return: None
        """

        # checkea que el índice del timer sea válido y si lo es crea el Timer
        if timer_index not in range(len(self.timer_list)):
            raise IndexError("Indice timer_index fuera de rango.")
        elif self.timeout > 0:
            self.timer_list[timer_index] = Timer(self.timeout, self._time_up_function, args=(timer_index,))

        # envía el mensaje contenido en data
        self.socket_udp.sendto(data, address)
        if self.timeout > 0:
            # echa a correr el timer recién creado
            self.timer_list[timer_index].start()

    def _time_up_function(self, timer_index: int) -> None:
        """ Función que llama cada objeto Timer en caso de cumplir su timeout.

        Esta función indica que el timout del timer asociado a timer_index debe
        ser anunciado, y añade el índice timer_index a la lista de
        timed_out_timers.

        :param timer_index: int
            índice del Timer en timer_list
        :return: None
        """
        self.announce_timeout[timer_index] = True
        self.timed_out_timers.append(timer_index)

    def recvfrom(self, buffer_size: int) -> tuple[bytes, tuple[str, int]]:
        """ Wrapper de la función recvfrom de python que permite el manejo de
        timers.

        Esta función se mantiene escuchando continuamente hasta que llegue un
        mensaje o se cumpla el tiempo de espera de algún Timer. En caso de que
        se cumpla el timeout de un Timer, lanza un TimeoutError indicando el
        índice del timer correspondiente. En caso de recibir un mensaje, lo
        retorna PERO no detiene ningún Timer.

        :param buffer_size: int
            tamaño del buffer de recepción.
        :return: tuple[bytes, tuple[str, int]]
            tupla que contiene el mensaje recibido en bytes y la dirección
            desde donde se recibió dicho mensaje.
        """
        # para manejar la recepción con timers es necesario mantenerse
        # escuchando con un while True.
        #
        # Esto ocurre porque se debe mantener el socket como no bloqueante
        # para poder revisar si es necesario levantar un error o no.
        while True:
            if True in self.announce_timeout:
                # si algún timer cumple su tiempo, se lanza un TimeoutError
                timer_index = self.announce_timeout.index(True)
                self.announce_timeout[timer_index] = False
                raise TimeoutError(f"Timer {timer_index}")
            try:
                # si se logra recibir algo retornamos (no se cancela ningún Timer)
                answer, address = self.socket_udp.recvfrom(buffer_size)
                return answer, address
            except BlockingIOError:
                # cada vez que el socket NO recibe algo, lanza BlockingIOError
                continue

    def get_stopped_timers(self) -> list[int]:
        """ Retorna la lista de índices de Timers que ya cumplieron su timeout.

        :return: list[int]
            lista de índices de Timers detenidos
        """
        return self.timed_out_timers

    def stop_timer(self, timer_index=0) -> None:
        """ Permite detener y resettear el objeto Timer asociado a timer_index.

        :param timer_index: int
            índice del Timer a detener. Su valor default es 0.
        :return: None
        """
        # primero se cancela el Timer para que detenga su ejecución.
        self.timer_list[timer_index].cancel()
        # luego se borra de las listas correspondientes
        self.timer_list[timer_index] = None
        if timer_index in self.timed_out_timers:
            self.timed_out_timers.remove(timer_index)
        self.announce_timeout[timer_index] = False

    def close(self) -> None:
        """ Wrapper de close.

        :return: None
        """
        self.socket_udp.close()


