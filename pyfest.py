import socket
import struct

class PyFest(object):
    def __init__(self, server, port=1314, password=None, buff=4096,
                 resp_term = 'ft_StUfF_keyOK\n'):
        """

        :param server: Server IP or DNS name
        :param port: festival server port
        :param password: festival server password if used
        :param buff: Buffer size
        :param resp_term: Expected transmition terminator
        :return:
        """
        # set class variables
        self.server = server
        self.port = port
        self.buff = buff
        
        # the damn key saying the communication is over
        self.resp_term = resp_term
        self.resp_term_len = len(self.resp_term)
        
        # create socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # start our connection
        self.s.connect((self.server, self.port))
        
        # If we supplied a password, send it over
        if password:
            self.s.send(password)
              
    def set_parameter(self, param, value):
        """
        :param param: parameter to set to send to festival server
        :param value: Value of parameter
        :return:
        """
        self.s.send("(Parameter.set '%s '%s)" % (param, value))
        return self.__get_rsp_code()()
        
    def get_wave_from_text(self, text):
        self.s.send('(tts_textall "%s" "nil")' % text)
        for l in self.__get_rsp_code()():
            yield l
    
    def __get_rsp_code(self):
        """

        :return: result of rsp code
        """
        rsp = self.s.recv(3)
        if rsp == 'LP\n':
            return self.__get_lp_result
        elif rsp == 'WV\n':
            return self.__get_wv_result
        elif rsp == 'ER\n':
            raise Exception
        elif rsp == 'OK\n':
            pass
        else:
            #how the...
            pass
        
    def set_timeout(self, time):
        """
        Set the timeout for the socket, by default this is unlimited

        :param time: time in seconds for socket to remain idle
        :type time: int
        :return: None
        """
        self.s.settimeout(time)
        
    def raw_recv(self):
        """
        Raw recieve on the socket
        :return: String server response using the buff variable to determine amount
        """
        return self.s.recv(self.buff)
    
    def __get_lp_result(self):
        """
        Internal function to pass import response

        :return:
        """

        tmp_buff = ''
        # While we do not see the end of the communication keep pulling
        while self.resp_term not in tmp_buff[-self.resp_term_len:]:
            data = self.s.recv(self.buff)
            tmp_buff += data
        
        # return what we found, minus the terminator
        return tmp_buff[:-self.resp_term_len]
        
    def __get_wv_result(self, wav_type = 'riff'):
        """
        Receives wave file from festival server

        :param wav_type: wave format to use
        :yeilds: raw wave buffer size at a time
        """
        # OK what does our header look like
        wav_header = self.s.recv(8)

        # Is it what we requested?
        if wav_header[0:4] == wav_type.upper():

            # How much music do we have?
            wav_size = struct.unpack('<L', wav_header[4:8])[0]

            # get ready
            count = 0

            # As long as we are not the same size as the header says
            while count < wav_size:

                # see how much we have left
                left_to_get = wav_size - count

                # If it is less than our buffer size, just grab what is left
                if left_to_get < self.buff:
                    data = self.s.recv(left_to_get)
                else:
                    data = self.s.recv(self.buff)

                # this our first time through?
                if count == 0:
                    yield wav_header + data

                # see what we got back and do our maths
                count += len(data)

                # write it out to the file
                yield data

    def close(self):
        """
        Closes the socket to festival

        :returns None
        """
        self.s.close()
        
