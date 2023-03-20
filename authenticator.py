import yaml

from streamlit_authenticator import SafeLoader, Authenticate


class Authenticator:
    def __init__(self) -> None:
        self.streamlitAuthenticator = None
        self.name = None
        self.authenticationStatus = False
        self.username = None
    
    def loadConfig(self, filePath, fileLoader):
        with open(filePath) as file:
            config = yaml.load(file, Loader=fileLoader)
        return config
    
    def authenticate(self, filePath='user_logins.yaml', fileLoader=SafeLoader):
        config = self.loadConfig(filePath, fileLoader)
        self.streamlitAuthenticator = Authenticate(config['credentials'],
                                                   config['cookie']['name'],
                                                   config['cookie']['key'],
                                                   config['cookie']['expiry_days'],
                                                   config['preauthorized'])
        self.name, self.authenticationStatus, self.username = self.streamlitAuthenticator.login('Login', 'main')