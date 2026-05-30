from typing import Optional
from enum import StrEnum 

class CongestionState(StrEnum):
    SLOW_START = "slow start"
    CONGESTION_AVOIDANCE = "congestion avoidance"

class CongestionControl:
    def __init__(self, MSS: int) -> None:
        # Indica estado actual de congestion 
        self.current_state: CongestionState = CongestionState.SLOW_START
        
        # Máx tamaño en bytes del área de datos de 
        # un segmento de congestión
        self.MSS: int = MSS
        
        # Tamaño de la ventana de congestión en bytes
        self.cwnd: float = float(MSS)
        
        # Slow start threshold
        #
        # current_state == "slow start"
        #   si cwnd >= ssthresh 
        #       => current_state = "congestion avoidance"
        # 
        # se define luego del primer timeout durante 
        # slow start
        self.ssthresh: Optional[int] = None 

    def get_cwnd(self) -> int:
        return int(self.cwnd)
    
    def get_MSS_in_cwnd(self) -> int:
        """
        Retorna la cantidad de MSS completos 
        que caben en la cwnd actual
        """
        return int(self.cwnd) // self.MSS

    def is_state_slow_start(self) -> bool:
        return self.current_state is CongestionState.SLOW_START

    def is_state_congestion_avoidance(self) -> bool:
        return not self.is_state_slow_start()

    def get_ssthresh(self) -> Optional[int]:
        return self.ssthresh

    def event_ack_received(self):
        """
        Maneja los cambios en la ventana de congestión (cwnd) 
        cuando se recibe un ACK de manera exitosa, 
        dependiendo del estado actual.
        """
        if self.is_state_slow_start():
            # Aumentamos la ventana en 1 MSS / ACK 
            self.cwnd += self.MSS

            # Verificamos si pasamos el threshold
            if self.ssthresh is not None and int(self.cwnd) >= self.ssthresh:
                self.current_state = CongestionState.CONGESTION_AVOIDANCE

        else:
            # En congestion avoidance el aumento es lineal (AIMD)
            mss_in_cwnd = self.get_MSS_in_cwnd()
            if mss_in_cwnd > 0:
                incr = self.MSS / mss_in_cwnd
                self.cwnd += incr

    def event_timeout(self):
        """
        Maneja los cambios de estado, de ventana de congestión 
        y del umbral (ssthresh) cuando ocurre un timeout.
        """
        # Actualizamos ssthresh a la mitad de la ventana actual 
        self.ssthresh = int(self.cwnd) // 2

        # Reiniciamos tamaño ventana a 1 MSS 
        self.cwnd = float(self.MSS) 

        # Cambiamos estado
        self.current_state = CongestionState.SLOW_START

