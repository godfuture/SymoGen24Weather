from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils


class SymoGen24:
    def __init__(self, ipaddr, port):
        self.modbus = ModbusClient(host=ipaddr, port=port, auto_open=True, auto_close=True)
        # self.modbus.debug(True)

        # Format:
        # "name : [register address, data type, unit 1]
        self.registers = {
        # Common Block Register   
            "SunspecSID" : [40001, "uint32", 1],
            "SunspecID" : [40070, "uint16", 1],
            "AC_Phase-A_Current" : [40074, "float", 1],
            "AC_Phase-B_Current" : [40076, "float", 1],
            "AC_Phase-C_Current" : [40078, "float", 1],
            "AC_Voltage_Phase-AB" : [40080, "float", 1],
            "AC_Voltage_Phase-BC" : [40082, "float", 1],
            "AC_Voltage_Phase-CA" : [40084, "float", 1],
            "AC_Voltage_Phase-A-N" : [40086, "float", 1],
            "AC_Voltage_Phase-B-N" : [40088, "float", 1],
            "AC_Voltage_Phase-C-N" : [40090, "float", 1],
            "AC_Output_Power" : [40092, "float", 1],
            "AC_Frequency" : [40094, "float", 1],
            "Cabinet_Temperature" : [40110, "float", 1],
            "Operating_State" : [40118, "uint16", 1],
        # Storage device (Battery)
            "Battery_capa" : [40143, "uint16", 1],

            "Battery_SunspecID" : [40314, "uint16", 1],
            "Battery_SoC" : [40322, "uint16", 1],
            "Battery_Status" : [40325, "uint16", 1],
        # Multiple MPPT
            "MPPT_SunspecID" : [40264, "uint16", 1],
            "MPPT_Current_Scale_Factor" : [40266, "uint16", 1],
            "MPPT_Voltage_Scale_Factor" : [40267, "uint16", 1],
            "MPPT_Power_Scale_Factor" : [40268, "uint16", 1],
            "MPPT_1_DC_Current" : [40283, "uint16", 1],
            "MPPT_1_DC_Voltage" : [40284, "uint16", 1],
            "MPPT_1_DC_Power" : [40285, "uint16", 1],
            "MPPT_1_Temperature" : [40290, "uint16", 1],
            "MPPT_1_State" : [40291, "uint16", 1],
            "MPPT_2_DC_Current" : [40303, "uint16", 1],
            "MPPT_2_DC_Voltage" : [40304, "uint16", 1],
            "MPPT_2_DC_Power" : [40305, "uint16", 1],
            "MPPT_2_Temperature" : [40310, "uint16", 1],
            "MPPT_2_State" : [40311, "uint16", 1],
        # Power Meter
            "Meter_SunspecID" : [40070, "uint16", 200],
            "Meter_Frequency" : [40096, "float", 200],
            "Meter_Power_Total" : [40098, "float", 200],
            "Meter_Power_L1" : [40100, "float", 200],
            "Meter_Power_L2" : [40102, "float", 200],
            "Meter_Power_L3" : [40104, "float", 200],
        }
                   
        self.modbus.unit_id(1)
        sunspecid = self.read_uint16(40070)
        if sunspecid != 113:
            print("Warning: Invalid SunspecID, wrong device ?")
                                      
    def read_uint16(self, addr):
        regs = self.modbus.read_holding_registers(addr-1, 1)
        if regs:
            return int(regs[0])
        else:
            print("read_uint16() - error")
            return False
      
    def read_uint32(self, addr):
        regs = self.modbus.read_holding_registers(addr-1, 2)
        if regs:
            return int(utils.word_list_to_long(regs, big_endian=True)[0])
        else:
            print("read_uint32() - error")
            return False
        
    def read_float(self, addr):
        regs = self.modbus.read_holding_registers(addr-1, 2)
        if not regs:
            print("read_float() - error")
            return False

        list_32_bits = utils.word_list_to_long(regs, big_endian=True)
        return float(utils.decode_ieee(list_32_bits[0]))

    def read_data(self, parameter):
        [register, datatype, unit_id] = self.registers[parameter]
        
        self.modbus.unit_id(unit_id)
        if datatype == "float":
            return self.read_float(register)
        elif datatype == "uint32":
            return self.read_uint32(register)
        elif datatype == "uint16":
            return self.read_uint16(register)
        else:
            return False

    def write_float(self, addr, value):
        floats_list = [value]
        b32_l = [utils.encode_ieee(f) for f in floats_list] 
        b16_l = utils.long_list_to_word(b32_l, big_endian=False)
        return self.modbus.write_multiple_registers(addr, b16_l)

    def write_uint16(self, addr, value):
        return self.modbus.write_single_register(addr, value)
   
    def write_data(self, parameter, value):
        [register, datatype, unit_id] = self.registers[parameter]
        
        self.modbus.unit_id(unit_id)
        if datatype == "float":
            return self.write_float(register, value)
        elif datatype == "uint16":
            return self.write_uint16(register, value)
        else:
            return False

    def print_all(self):
        print("Show all registers:")
        for name, params in self.registers.items():
            value = self.read_data(name)
            print("{0:d}: {1:s} - {2:2.1f}".format(params[0], name, value))
    
    # To search for undocument registers.... 
    def print_raw(self):
        print("Raw read 1000-2000:")
        for i in range(1000,2000,1):
            value = self.read_float(i)
            if value:
                print("{0:d}: {1:2.1f}".format(i, value))
            #else:
            #    print("{0:d}: error".format(i))

    def get_mppt_power(self):
        mpppt_1_power = self.read_data('MPPT_1_DC_Power')
        mpppt_2_power = self.read_data('MPPT_2_DC_Power')
        power_scale = 10**(self.read_data('MPPT_Power_Scale_Factor')-65536)
        return [mpppt_1_power * power_scale, mpppt_2_power * power_scale]
        
# Test program
if __name__ == "__main__":
    
    gen24 = SymoGen24(ipaddr="fronius.ip", port="502")
    
    # Sunspec ID (should be 113)
    print(gen24.read_uint16(40070))
    # Current AC Output Power
    print(gen24.read_float(40092))
    
    print(gen24.read_data("SunspecID"))
        
    #gen24.print_all()
    # gen24.print_raw()

    print(gen24.read_uint16(40069))

    # print(gen24.modbus.unit_id())
    
    # gen24.modbus.unit_id(200)

    # print(gen24.read_uint16(40070))
    # print(gen24.read_float(40098))
    
    print(gen24.get_mppt_power())
    
    # gen24.modbus.unit_id(1)
