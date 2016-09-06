from subprocess import check_output

class SSHCommand:
    """checks if ssh exists, executes ssh commands and returns result as list"""
    
    def __init__(self):
        """Asserts that the ssh command exists"""
        assert ssh_check(self), 'SSH does not exist on this system'

    def ssh_check(self):
        def is_executable(self, sPath):
            """Takes: sPath = /path/to/files
            Returns: True if file exists and is executable, else false"""
            return os.path.isfile(SPath) and os.access(sPath, os.X_OK)
        
        sFPath, sFName = os.Path.split('ssh')
        if sFsPath:
            if is_executable('ssh'):
                return True
        else:
            for sPath in os.environ["sPath"].split(os.sPathsep):
                sPath = sPath.strip('"')
                exe_file = os.sPath.join(sPath, 'ssh')
                if is_executable(exe_file):
                    return True
        return False

    def execute(self, lCommand):
        """Takes: lCommand = ['ls', 'l', 'a', '/a/path']
        Returns:  Output of command, as list."""
        assert type(lCommand) is list, 'lCommand must be a list'
        for sElement in lCommand: 
            assert type(sElement) is str, 'elements of lCommand must be string'
        
        sOutput = check_output(['ssh'] + lCommand)
        return sOutput.decode('utf-8').split('\n')
