class Device():
    def __init__(self, obj) -> None:
        self.obj = obj
    
    def get_device_id(self):
        return self.obj["deviceId"]
    
    def get_serialnumber(self):
        return self.obj["serialNumber"]

    def get_value(self, key):
        return self.obj.get(key, 'SAKNAS')
