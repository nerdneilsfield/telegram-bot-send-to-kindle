import redis



class Users(object):
    def __init__(self, host, port, password=None):
        self.con = redis.StrictRedis(host=host, port=port, password=password)
    def get(self, id):
        return self.con.get(id)
    def remove(self, id):
        try:
            self.con.delete('id')
        except:
            return False
        finally:
            return True
    def set(self, id, email):
        try:
            self.con.set(id, email)
        except:
            return False
        finally:
            return True
    def exists(self, id):
        return self.con.exists(id)