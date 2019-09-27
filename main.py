'''
(keep-lines "^def .*:")
'''

import logging
from logging.handlers import RotatingFileHandler
import time
import json
import requests
import os.path
import serial
from controllerstate import *
from userpass import getUsername, getPassword

CURRENT_VERSION = 14
USERNAME = getUsername()
PASSWORD = getPassword()
URL_SERVER = 'http://emiliozelione2018.pythonanywhere.com/'
requests.get(
    URL_SERVER + 'requests?running_version=' + str(CURRENT_VERSION) +
    '&username=' + USERNAME + '&password=' + PASSWORD)

# irrigation, fertilization and inyection
BASE_PROGFERT = 1600 + 8192
BASE_PROGRIEGO = 0 + 8192
BASE_PROGRIEGO_STATE = 0x8D8 + 8192
BASE_PROGRIEGO_STATE_RAM = 0x293
BASE_CONFIGINYECTORES = 1960 + 8192
# IO
BASE_ADDINYECTORS = 2501 + 8192
BASE_ADDFILTROS = 2509 + 8192
BASE_ADDACTUADORES = 2517 + 8192
BASE_PRIVALEC = 2530 + 8192
BASE_PRIVALBYTES = 2538 + 8192
BASE_V1AV16 = 2421 + 8192
BASE_V17AV32 = 2437 + 8192
BASE_V33AV48 = 2453 + 8192
BASE_V49AV64 = 2469 + 8192
BASE_V65AV80 = 2485 + 8192
# alarm config
BASE_CONFIGALARMAS = 2237 + 8192
BASE_CONFIGECPHPARAMS = 2224 + 8192
# alarms
BASE_FERT_NO_CONTROL_LACK_FERT_RAM = 0xBC8
# error ec, error ph, dangerous ec, dangerous ph
BASE_ALARM_EC_PH_RAM = 0xBCA
# error flow, dangerous flow, no water, irr out of control
BASE_ALARM_FLOW_RAM = 0xBD6
# high pressure, low pressure
BASE_ALARM_PRESSURE_RAM = 0xBD3
# actuators
# irr pump, fert pump, blender, alarm
BASE_ACTUATORS_RAM = 0xB1E
BASE_ACTUATORS_INYECTOR_RAM = 0xB1C
# other configs
BASE_FLOWMETER = 2204 + 8192
BASE_BLOWER = 0x8A0 + 8192
BASE_BOOSTER = 0x9FE + 8192
BASE_MANUAL_IRRIGATION = 2414 + 8192
BASE_MANUAL_IRRIGATION_PROG = 0x1DB
BASE_TIME_RESTART = 2556 + 8192
BASE_TOFF_INYECTOR = 2420 + 8192
# solape
BASE_SOLAPE = 2024 + 8192
BASE_SOLAPE_MMSS = 2184 + 8192
# backflushing
BASE_ADDRETROLAVADO = 2213 + 8192

# terminal stats
# irrigation - total a regar h - total a regar m - agua antes h - agua antes m - agua dp h - agua dp m - unidad
BASE_IRRIGATION = 0x1F5
BASE_FERT = 0x168
BASE_NEXT_PROG = 0x1DA
# 3 bytes
BASE_M3 = 0xB0D
BASE_IRRIGATION_TIME = 0x203
BASE_TOTAL_IRRIGATION = 0xB0D
BASE_MEASURED_FLOW = 0xA24
# 2 bytes
BASE_C_PROG = 0x83C
BASE_P1_P2 = 0x394 # float
BASE_EC_PH_MEASURED = 0x392 # float EC y pH
BASE_EC_PH_ASKED = 0x0224 # float ph y EC
BASE_EC_PH_AVERAGE = 0x28F # float primero pH y dp EC
# 96 byes / 48 registers
# 32 bytes first 2 vars
BASE_INYECTOR_STATS_1_2 = 0xA04
BASE_INYECTOR_STATS_3 = 0xA5C
BASE_INYECTOR_STATS_4 = 0xA78
BASE_INYECTOR_STATS_5 = 0xAF2
BASE_VALVES_STATS = 0xBA5
# termstats filters
# filtros del 1 al 8, 1 bit x filtro. byte 2, 5to bit es sustain valve
BASE_FILTERS_RAM = 0xBB0
# 0: No retrolavando, 1: Presion diferencial, 2: Por tiempo, 3: Manual
BASE_FILTER_CLEANING_MOTIVE = 0x37A
# hh y mm
BASE_NEXT_WASHER = 0x377
# bit 0
BASE_NO_WASHER = 0x375
# bit 0
BASE_WASHER_STATE = 0x370
# buttons stop wash (first byte) y wash now (segundo byte)
BASE_BUTTON_WASH_NOW = 0x37D

BASE_BOOKS_TOTAL = 0x65B

BASE_BOOKS_NUMBER = 0x8E5
BASE_BOOKS_SEND_KEY = 0x8E0
BASE_KEYS_BOOK = [0x73, 0x11, 0x23, 0x7E]
BASE_BOOKS_DATE = 0xC3D
BASE_BOOKS_INYECTORS = 0xC46
BASE_BOOKS_TOTAL_TIME = 0xC5E
BASE_BOOKS_TOTAL_QTY = 0xC61
BASE_BOOKS_PH_EC_AVG = 0xC64
BASE_BOOKS_IRR_FERT = 0xC44

# escribir el primero en 0 y el otro en el prog de riego
BASE_IRR_INFO = 0x8E5
BASE_IRR_INFO_SEND_KEY = 0x8E0
BASE_KEYS_INFO = [0xD2, 0x48, 0x53, 0xF7]
# 3 bytes, consecutivos 
BASE_IRR_INFO_INYECTORS = 0xC3D
# 0: golpes, 2:m3 alto, 3:m3 bajo, 4:hh acumulada, 5:mm acc, 
BASE_IRR_INFO_KICKS = 0xC20
# 0: HH, 1:MM, 
BASE_IRR_INFO_HH_MM_ULTIMO_RIEGO = 0x304
# 0-1: ph, 2-3:ec ambos float
BASE_IRR_INFO_PH_EC_PROMEDIO = 0xC35

BASE_START_BUTTON = 0x1BC # setear bit 5
BASE_STOP_BUTTON = 0x1DC # setear bit 6

TOTAL_FERT = 20
TOTAL_INY = 8
TOTAL_IRR = 50
DIRTY_ADD = 4234
TIME_UPDATE = 0.1
FILEPATH_SAVE = "/home/pi/fertiriego-rpi/controller.bin"

write_irrProg = [False] * 50
write_fertProg = [False] * 20
write_ConfIny = [False] * 8
write_ConfigAl = False
write_configIO = False
write_backflush = False
write_solape = False
write_other = False

terminalSerial = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.2)
# 
def fetch_json():
    response = requests.get(
        URL_SERVER + 'requests?all&username=' +
        USERNAME + '&password=' + PASSWORD)
    dataJson = response.json()
    return (dataJson)

def fetch_last_update():
    response = requests.get(
        URL_SERVER +
        'requests?updated_when_server&username=' +
        USERNAME +
        '&password=' +
        PASSWORD)
    dataJson = response.json()
    return (dataJson['update'], dataJson['updated_by'])

def is_set(x, n):
    val = x & 2 ** n != 0
    if val:
        return 1
    else:
        return 0

def check_login():
    response = requests.get(
        URL_SERVER +
        'login?username=' +
        USERNAME +
        '&password=' +
        PASSWORD)
    dataJson = response.json()
    return (dataJson['ok'])

def read_dirty():
    regs = read_registers(DIRTY_ADD, 1)
    if regs[0] == 186:
        return True
    else:
        return False

def write_dirty():
    val = [0, 0]
    write_registers(DIRTY_ADD, 1, val)

def read_registers(Add, nRegs):
    byteList = []
    AddH = int(Add / 256)
    AddL = Add % 256
    Encabezado = [1, 3, AddH, AddL, 0, nRegs]  # Son 1Registros
    # Tengo la lista en bytes, Aplicar los CRC
    byteList = Encabezado + byteList
    listaCRC = calculate_crc(byteList)
    byteList = byteList + listaCRC  # Le agrega los bytes de CRC
    incoming = []
    Total_in = nRegs * 2 + 5
    while (len(incoming) < (Total_in)):
        terminalSerial.write(byteList)
        terminalSerial.flush()
        incoming = terminalSerial.read(Total_in)
        BytesIn = bytes2integer(incoming)
        CRC_in = BytesIn[(Total_in - 2):Total_in]
        del BytesIn[-2:]  # borra los 2 ultimos elementos
        listaCRC = calculate_crc(BytesIn)
    if (listaCRC == CRC_in):
        del BytesIn[0:3]  # borra del 0 al 3 no inclusive
        return BytesIn
    else:
        return None

def write_registers(Add, nRegs, byteList):
    AddH = int(Add / 256)
    AddL = Add % 256
    Encabezado = [1, 16, AddH, AddL, 0, nRegs, nRegs * 2]
    byteList = Encabezado + byteList
    listaCRC = calculate_crc(byteList)
    byteList = byteList + listaCRC
    # Le agrega los bytes de CRC
    incoming = []
    Total_in = 8
    # Cuando Escribis Recibis 8 Bytes Fijos
    while (len(incoming) < (Total_in)):
        terminalSerial.write(byteList)
        terminalSerial.flush()
        incoming = terminalSerial.read(Total_in)
        BytesIn = bytes2integer(incoming)
        CRC_in = BytesIn[(Total_in - 2):Total_in]
        del BytesIn[-2:]  # borra los 2 ultimos elementos
        listaCRC = calculate_crc(BytesIn)
    if (listaCRC == CRC_in):
        return True
    else:
        return False

def read_from_controller_inyectors(ci):
    if ci in cs.allInyection:
        ConfigInyL = cs.allInyection[ci]
    else:
        ConfigInyL = InyectionProgram()
        ConfigInyL.program = ci
    ConfigIny = InyectionProgram()
    write_ConfIny[ci - 1] = False
    Add = BASE_CONFIGINYECTORES + (ci - 1) * 8
    byteList = []
    byteList = read_registers(Add, 4)
    function = byteList[0]
    flow = byteList[1] * 256 + byteList[2]
    timeOn = byteList[3]/10
    mlPulso = byteList[4] * 256 + byteList[5]
    simulator = byteList[6]
    maxDeviation = byteList[7]
    ConfigIny.program = ci
    ConfigIny.flow = flow
    ConfigIny.time_on = timeOn
    ConfigIny.function = function
    ConfigIny.litres_pulse = mlPulso
    if simulator == 0:
        ConfigIny.simulator = False
    else:
        ConfigIny.simulator = True
    ConfigIny.max_deviation = maxDeviation
    if ConfigInyL != ConfigIny:
        write_ConfIny[ci - 1] = True
        cs.allInyection[ci] = ConfigIny

def read_from_controller_fertilization(pf):
    if pf in cs.allFertilization:
        FertProgL = cs.allFertilization[pf]
    else:
        FertProgL = FertilizationProgram()
    FertProg = FertilizationProgram()
    write_fertProg[pf - 1] = False
    Add = BASE_PROGFERT + (pf - 1) * 18
    byteList = []
    byteList = read_registers(Add, 9)
    i = 0
    Val = [0] * 10
    while (i < 8):
        Val[i] = float(byteList[2 * i] * 256 + byteList[2 * i + 1])
        if pf in cs.allInyection and (cs.allInyection[pf].function == 5 or cs.allInyection[pf].function == 6 or cs.allInyection[pf].function == 7):
            Val[i] = Val[i] / 10
        i = i + 1
    Val[8] = byteList[16] / 10
    Val[9] = byteList[17] / 10
    FertProg.program = pf
    FertProg.values_1 = Val[0]
    FertProg.values_2 = Val[1]
    FertProg.values_3 = Val[2]
    FertProg.values_4 = Val[3]
    FertProg.values_5 = Val[4]
    FertProg.values_6 = Val[5]
    FertProg.values_7 = Val[6]
    FertProg.values_8 = Val[7]
    FertProg.ec = Val[8]
    FertProg.ph = Val[9]
    if FertProgL != FertProg:
        write_fertProg[pf - 1] = True
        cs.allFertilization[pf] = FertProg

def read_from_solape():
    global write_solape
    solapeNew = ValveSolape()
    byteList = []
    offset = 0
    while offset < (80+80)/2:
        byteList += read_registers(BASE_SOLAPE+offset, 10)
        offset += 10
    flow, solape, time = [], [], []
    i = 0
    while i < 80:
        flow.append(byteList[i])
        solape.append(byteList[i+80])
        i += 1
    i = 0
    byteList = read_registers(BASE_SOLAPE_MMSS, 10)
    while i < 20:
        # negative
        if byteList[i] >= 128:
            t = byteList[i]*256 + byteList[i+1]
            t = 65536 - t
            t /= 100.0
            time.append(-t)
        else:
            t = byteList[i]*256 + byteList[i+1]
            t /= 100
            time.append(t)
        i += 2
    solapeNew.flow = ','.join(map(str, flow))
    solapeNew.solape = ','.join(map(str, solape))
    solapeNew.time = ','.join(map(str, time))
    if cs.solape != solapeNew:
        write_solape = True
        cs.solape = solapeNew

def read_from_alarms():
    byteList = read_registers(BASE_FERT_NO_CONTROL_LACK_FERT_RAM, 1)
    fert_no_control = []
    fert_lack = []
    for i in range(0, 8):
        fert_no_control.append(is_set(byteList[0], i))
        fert_lack.append(is_set(byteList[1], i))
    cs.alarm.fertilization_deficit = ','.join(map(str, fert_lack))
    cs.alarm.fertilization_desc = ','.join(map(str, fert_no_control))
    byteList = read_registers(BASE_ALARM_EC_PH_RAM, 1)
    cs.alarm.ec_error = is_set(byteList[0], 0)
    cs.alarm.ph_error = is_set(byteList[0], 1)
    cs.alarm.ec_danger = is_set(byteList[0], 2)
    cs.alarm.ph_danger = is_set(byteList[0], 3)
    byteList = read_registers(BASE_ALARM_FLOW_RAM, 1)
    cs.alarm.flow_error = is_set(byteList[0], 0)
    cs.alarm.dangerous_flow = is_set(byteList[0], 1)
    cs.alarm.no_water = is_set(byteList[0], 2)
    cs.alarm.irrigation_out_of_controls = is_set(byteList[0], 3)
    byteList = read_registers(BASE_ALARM_PRESSURE_RAM, 1)
    cs.alarm.high_pressure = is_set(byteList[0], 0)
    cs.alarm.low_pressure = is_set(byteList[0], 1)

def read_from_other_configs():
    global write_other
    otherNew = OtherConfigs()
    byteList = read_registers(BASE_MANUAL_IRRIGATION, 2)
    byteListProg = read_registers(BASE_MANUAL_IRRIGATION_PROG, 1)
    otherNew.manual_irrigation_program = byteListProg[0]
    otherNew.manual_irrigation_units = byteList[0]
    otherNew.manual_irrigation_water_1 = byteList[2]
    otherNew.manual_irrigation_water_2 = byteList[3]
    byteList = read_registers(BASE_TOFF_INYECTOR, 1)
    otherNew.toff_inyector = float(byteList[0])/10
    byteList = read_registers(BASE_FLOWMETER, 2)
    otherNew.flow_meter_1 = byteList[0]*256 + byteList[1]
    otherNew.flow_meter_2 = byteList[2]
    byteList = read_registers(BASE_BLOWER, 1)
    otherNew.blower_1 = byteList[0]
    otherNew.blower_2 = byteList[1]
    byteList = read_registers(BASE_TIME_RESTART, 1)
    otherNew.time_restart_program_1 = byteList[0]
    otherNew.time_restart_program_2 = byteList[1]
    byteList = read_registers(BASE_BOOSTER, 1)
    otherNew.booster_pump = byteList[0]
    if cs.other != otherNew:
        write_other = True
        cs.other = otherNew

def read_from_backflushing():
    global write_backflush
    backFlushing = cs.back_flushing
    backFlushingNew = BackFlushing()
    byteList = []
    byteList = read_registers(BASE_ADDRETROLAVADO, 5)
    backFlushingNew.difference_backflush_kg = float(byteList[0])/10
    backFlushingNew.time_between_flushing_hours = byteList[1]
    backFlushingNew.time_between_flushing_minutes = byteList[2]
    backFlushingNew.time_between_station_min = byteList[3]
    backFlushingNew.time_between_station_sec = byteList[4]
    backFlushingNew.pause_between_filtering_secs = byteList[5]
    backFlushingNew.amount_of_filters = byteList[6]
    backFlushingNew.times_wash_before_pd_alarm = byteList[7]
    backFlushingNew.delay_differential_pressure = byteList[8]
    backFlushingNew.wait_after_sustain = byteList[9]
    if backFlushing != backFlushingNew:
        write_backflush = True
        cs.back_flushing = backFlushingNew

def read_from_controller_irrigation(pr):
    if pr in cs.allIrrigation:
        ProgRiegoL = cs.allIrrigation[pr]
    else:
        ProgRiegoL = IrrigationProgram()
    write_irrProg[pr - 1] = False
    ProgRiego = IrrigationProgram()
    Add = BASE_PROGRIEGO + (pr - 1) * 32
    listaA = read_registers(Add, 8)
    ProgRiego.program = pr

    ProgRiego.water_total_1 = listaA[0]
    ProgRiego.water_total_2 = listaA[1]
    ProgRiego.water_before_1 = listaA[2]
    ProgRiego.water_before_2 = listaA[3]
    ProgRiego.water_after_1 = listaA[4]
    ProgRiego.water_after_2 = listaA[5]
    ProgRiego.time_between_1 = listaA[6]
    ProgRiego.time_between_2 = listaA[7]
    ProgRiego.time_start_1 = listaA[8]
    ProgRiego.time_start_2 = listaA[9]
    ProgRiego.units = listaA[10]
    ProgRiego.fertilization_program = listaA[11]
    ProgRiego.kicks = listaA[12]
    ProgRiego.condition_program = listaA[13]
    Add = BASE_PROGRIEGO + (pr - 1) * 32 + 16
    listaB = read_registers(Add, 8)
    listaDias = listaA[14:16] + listaB[0:5]
    i = 0
    for elem in listaDias:
        if i == 0:
            cadDias = str(elem)
        else:
            cadDias = cadDias + ',' + str(elem)
        i = i + 1
    del listaB[0:5]  # borra del 0 al 5 no inclusive
    
    ProgRiego.days = cadDias
    Cadvalves = decode_valves(listaB)
    ProgRiego.valves = Cadvalves

    byteList = read_registers(BASE_PROGRIEGO_STATE+pr-1, 1)
    ProgRiego.state = byteList[0]
    ProgRiego.status = ProgRiegoL.status
    if ProgRiego != ProgRiegoL:
        write_irrProg[pr - 1] = True
        logger.info("PROGRAM IRRIGATION DEBUG")
        logger.info(str(ProgRiegoL.__dict__))
        logger.info(str(ProgRiego.__dict__))
        cs.allIrrigation[pr] = ProgRiego

def read_from_controller_config_alarms():
    ConfigAl = cs.alarm_config
    ConfigAlW = AlarmConfig()
    global write_ConfigAl
    write_ConfigAl = False
    listaA = read_registers(BASE_CONFIGECPHPARAMS, 6)
    listaB = read_registers(BASE_CONFIGALARMAS - 1, 7)
    listaC = read_registers(BASE_CONFIGALARMAS + 13, 6)
    ConfigAlW.delay_secs_if_diff_ec_more_1 = listaA[0]
    ConfigAlW.delay_secs_if_diff_ec_more_05 = listaA[1]
    ConfigAlW.delay_secs_if_diff_ec_more_03 = listaA[2]
    ConfigAlW.coefficient_correction_ec_more_1 = listaA[3]
    ConfigAlW.coefficient_correction_ec_more_05 = listaA[4]
    ConfigAlW.coefficient_correction_ec_more_03 = listaA[5]
    ConfigAlW.delay_secs_if_diff_ph_more_1 = listaA[6]
    ConfigAlW.delay_secs_if_diff_ph_more_05 = listaA[7]
    ConfigAlW.delay_secs_if_diff_ph_more_03 = listaA[8]
    ConfigAlW.coefficient_correction_ph_more_1 = listaA[9]
    ConfigAlW.coefficient_correction_ph_more_05 = listaA[10]
    ConfigAlW.coefficient_correction_ph_more_03 = listaA[11]
    ConfigAlW.secs_first_ec_correction = listaB[0]
    ConfigAlW.secs_first_ph_correction = listaB[0]
    ConfigAlW.deviation_warning_max_error_flow = listaB[1]
    ConfigAlW.delay_alarms_ec_ph_secs = listaB[2]
    ConfigAlW.delay_alarm_ph_dangerous_secs = listaB[3]
    ConfigAlW.delay_alarm_ec_dangerous_secs = listaB[4]
    ConfigAlW.delay_alarm_high_pressure_kg = listaB[5]
    ConfigAlW.delay_alarm_low_pressure_secs = listaB[6]
    ConfigAlW.delay_alarm_flow_secs = listaB[7]
    ConfigAlW.max_diff_warning_error_ec = float(listaB[8])/10
    ConfigAlW.max_diff_warning_error_ph = float(listaB[9])/10
    ConfigAlW.max_deviation_under_ph = float(listaB[10])/10
    ConfigAlW.max_deviation_over_ec = float(listaB[11])/10
    ConfigAlW.level_alarm_high_pressure_kg = float(listaB[12])/10
    ConfigAlW.level_alarm_low_pressure_kg = float(listaB[13])/10

    ConfigAlW.function_alarm_fertilizer_discontinued = listaC[1]
    ConfigAlW.function_alarm_ec_ph_dangerou = listaC[2]
    ConfigAlW.function_alarm_high_pressure = listaC[3]
    ConfigAlW.function_alarm_dangerous_flow = listaC[4]
    ConfigAlW.function_alarm_no_fertilization = listaC[5]
    ConfigAlW.function_alarm_no_water = listaC[6]
    ConfigAlW.pulses_fertilizer_no_control = listaC[7]
    ConfigAlW.pulses_needs_fertilizer = listaC[8]
    ConfigAlW.max_seconds_between_water_pulses = listaC[9]
    ConfigAlW.over_dangerous_flow_percentage = listaC[10]

    if ConfigAlW != ConfigAl:
        write_ConfigAl = True
        cs.alarm_config = ConfigAlW

def read_from_controller_input_output():
    ConfigIO_w = IOConfig()
    ConfigIO = cs.config_io
    global write_configIO
    write_configIO = False
    listaA = read_registers(BASE_ADDINYECTORS, 4)
    ConfigIO_w.inyection = ','.join(str(e) for e in listaA)
    listaA = read_registers(BASE_ADDFILTROS, 4)
    ConfigIO_w.filters = ','.join(str(e) for e in listaA)
    listaA = read_registers(BASE_ADDACTUADORES, 4)
    ConfigIO_w.actuators = ','.join(str(e) for e in listaA)
    listaA = read_registers(BASE_V1AV16, 8)
    ConfigIO_w.valves1to16 = ','.join(str(e) for e in listaA)
    listaA = read_registers(BASE_V17AV32, 8)
    ConfigIO_w.valves17to32 = ','.join(str(e) for e in listaA)
    listaA = read_registers(BASE_V33AV48, 8)
    ConfigIO_w.valves33to48 = ','.join(str(e) for e in listaA)
    listaA = read_registers(BASE_V49AV64, 8)
    ConfigIO_w.valves49to64 = ','.join(str(e) for e in listaA)
    listaA = read_registers(BASE_V65AV80, 8)
    ConfigIO_w.valves65to80 = ','.join(str(e) for e in listaA)
    listaA = read_registers(BASE_PRIVALEC, 4)
    listaB = read_registers(BASE_PRIVALBYTES, 8)
    analog_input_1 = listaA[0:4]
    analog_input_2 = listaA[4:8]
    listaRead = []
    i = 0
    while (i < 8):
        listaRead.append(listaB[2 * i] * 256 + listaB[2 * i + 1])
        i = i + 1
    analog_input_3 = listaRead[0:4]
    analog_input_4 = listaRead[4:8]
    ConfigIO_w.analog_input_1 = ','.join(str(e) for e in analog_input_1)
    ConfigIO_w.analog_input_2 = ','.join(str(e) for e in analog_input_2)
    ConfigIO_w.analog_input_3 = ','.join(str(e) for e in analog_input_3)
    ConfigIO_w.analog_input_4 = ','.join(str(e) for e in analog_input_4)
    if (ConfigIO != ConfigIO_w):
        write_configIO = True
        cs.config_io = ConfigIO_w

def decode_valves(ListaValves):
    CantValv = 0
    CadValv = ""
    i = 0
    while (i < 9):  # Registros
        j = 0
        while (j < 8):  # bits
            peso = ListaValves[i] & (2 ** j)
            valv = (i * 8) + j + 1
            if (peso != 0):
                if (CantValv == 0):
                    CadValv = str(valv)
                else:
                    CadValv = CadValv + ',' + str(valv)
                CantValv = CantValv + 1
            j = j + 1
        i = i + 1
    return (CadValv)

def write_controller_fertilization(pf):
    FertProg = cs.allFertilization[pf]
    newList = []
    byteList = []
    newList.append(int(FertProg.values_1))
    newList.append(int(FertProg.values_2))
    newList.append(int(FertProg.values_3))
    newList.append(int(FertProg.values_4))
    newList.append(int(FertProg.values_5))
    newList.append(int(FertProg.values_6))
    newList.append(int(FertProg.values_7))
    newList.append(int(FertProg.values_8))
    EC = FertProg.ec * 10
    pH = FertProg.ph * 10
    newList.append(int(EC) * 256 + int(pH))
    i = 1
    for elem in newList:
        if i in cs.allInyection and (cs.allInyection[i].function == 5 or cs.allInyection[i].function == 6 or cs.allInyection[i].function == 7):
            elem *= 10
        byteList.append(int(elem / 256))
        byteList.append(elem % 256)
    Add = BASE_PROGFERT + (pf - 1) * 18
    write_registers(Add, 9, byteList)

def write_controller_input_output():
    listaSal = []
    listaSal = cs.config_io.inyection.split(',')
    listaSal = [int(i) for i in listaSal]
    write_registers(BASE_ADDINYECTORS, 4, listaSal)
    listaSal = []
    listaSal = cs.config_io.filters.split(',')
    listaSal = [int(i) for i in listaSal]
    write_registers(BASE_ADDFILTROS, 4, listaSal)
    listaSal = []
    listaSal = cs.config_io.actuators.split(',')
    listaSal = [int(i) for i in listaSal]
    write_registers(BASE_ADDACTUADORES, 4, listaSal)
    listaSal = []
    listaSal = cs.config_io.valves1to16.split(',')
    listaSal = [int(i) for i in listaSal]
    write_registers(BASE_V1AV16, 8, listaSal)
    listaSal = []
    listaSal = cs.config_io.valves17to32.split(',')
    listaSal = [int(i) for i in listaSal]
    write_registers(BASE_V17AV32, 8, listaSal)
    listaSal = []
    listaSal = cs.config_io.valves33to48.split(',')
    listaSal = [int(i) for i in listaSal]
    write_registers(BASE_V33AV48, 8, listaSal)
    listaSal = []
    listaSal = cs.config_io.valves49to64.split(',')
    listaSal = [int(i) for i in listaSal]
    write_registers(BASE_V49AV64, 8, listaSal)
    listaSal = []
    listaSal = cs.config_io.valves65to80.split(',')
    listaSal = [int(i) for i in listaSal]
    write_registers(BASE_V65AV80, 8, listaSal)
    listaSal = []
    listaSal = cs.config_io.valves65to80.split(',')
    listaSal = [int(i) for i in listaSal]
    write_registers(BASE_V65AV80, 8, listaSal)
    import math
    # Leer los analog_inputs Pedirle a Fernando que cambie los labels
    listaSalA = []
    listaSalA = cs.config_io.analog_input_1.split(',')
    listaSalA = [math.floor(float(i)/10) for i in listaSalA]
    listaSalB = []
    listaSalB = cs.config_io.analog_input_2.split(',')
    listaSalB = [math.floor(float(i)/10) for i in listaSalB]
    listaSalC = []
    listaSalC = cs.config_io.analog_input_3.split(',')
    listaSalC = [int(i) for i in listaSalC]
    listaSalD = []
    listaSalD = cs.config_io.analog_input_4.split(',')
    listaSalD = [int(i) for i in listaSalD]
    listaSal2 = listaSalC + listaSalD
    listaSal1 = listaSalA + listaSalB
    write_registers(BASE_PRIVALEC, 4, listaSal1)
    i = 0
    listaBytes = [0] * 16
    while (i < 8):
        listaBytes[i * 2] = int(listaSal2[i] / 256)
        listaBytes[i * 2 + 1] = listaSal2[i] % 256
        i = i + 1
    write_registers(BASE_PRIVALBYTES, 8, listaBytes)

def write_other_configs():
    otherConfs = cs.other
    byteList = []
    import math
    buffBytes = read_registers(BASE_FLOWMETER+2, 1)
    byteList.append(int(otherConfs.flow_meter_1/256))
    byteList.append(otherConfs.flow_meter_1 % 256)
    byteList.append(otherConfs.flow_meter_2)
    byteList.append(buffBytes[1])
    write_registers(BASE_FLOWMETER, 2, byteList)
    buffBytes = read_registers(BASE_TOFF_INYECTOR, 1)
    byteList = []
    byteList.append(int(cs.other.toff_inyector*10))
    byteList.append(buffBytes[1])
    write_registers(BASE_TOFF_INYECTOR, 1, byteList)
    buffBytes = read_registers(BASE_MANUAL_IRRIGATION, 1)
    byteList = []
    byteList.append(cs.other.manual_irrigation_units)
    byteList.append(buffBytes[1])
    byteList.append(cs.other.manual_irrigation_water_1)
    byteList.append(cs.other.manual_irrigation_water_2)
    write_registers(BASE_MANUAL_IRRIGATION, 2, byteList)
    byteListProg = read_registers(BASE_MANUAL_IRRIGATION_PROG, 1)
    byteListProg[0] = cs.other.manual_irrigation_program
    write_registers(BASE_MANUAL_IRRIGATION_PROG, 1, byteListProg)
    byteList = []
    byteList.append(cs.other.blower_1)
    byteList.append(cs.other.blower_2)
    write_registers(BASE_BLOWER, 1, byteList)
    byteList = []
    byteList.append(cs.other.time_restart_program_1)
    byteList.append(cs.other.time_restart_program_2)
    write_registers(BASE_TIME_RESTART, 1, byteList)
    secondByte = read_registers(BASE_BOOSTER, 1)
    byteList = []
    byteList.append(cs.other.booster_pump)
    byteList.append(secondByte[1])
    write_registers(BASE_BOOSTER, 1, byteList)


def write_controller_inyection(iny):
    byteList = []
    Inyector = cs.allInyection[iny]
    CaudMaxVenturi = Inyector.flow
    TON = Inyector.time_on
    mlPulse = Inyector.litres_pulse
    MaxDesvio = Inyector.max_deviation
    Simular = Inyector.simulator
    byteList.insert(0, Inyector.function)
    byteList.insert(1, int(CaudMaxVenturi / 256))
    byteList.insert(2, int(CaudMaxVenturi % 256))
    byteList.insert(3, int(TON*10))
    byteList.insert(4, int(mlPulse / 256))
    byteList.insert(5, int(mlPulse % 256))
    byteList.insert(6, int(Simular))
    byteList.insert(7, int(MaxDesvio))
    Add = BASE_CONFIGINYECTORES + (iny - 1) * 8
    write_registers(Add, 4, byteList)

def write_controller_irrigation(pr):
    byteList = []
    lista_Valv = []
    ProgRiego = cs.allIrrigation[pr]
    RegistrosValvulas = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    if (ProgRiego.valves != ''):
        lista_Valv = ProgRiego.valves.split(',')
        i = 0
        for elem in lista_Valv:
            bit = (int(elem) - 1) % 8
            indice = int((int(elem) - 1) / 8)
            RegistrosValvulas[indice] = RegistrosValvulas[indice] | (2 ** bit)
            i = i + 1
    RegistrosDays = []
    if (ProgRiego.days != ''):
        lista_days = ProgRiego.days.split(',')
        for d in lista_days:
            RegistrosDays.append(d)
    i = 0
    byteList.insert(0, ProgRiego.water_total_1)
    byteList.insert(1, ProgRiego.water_total_2)
    byteList.insert(2, ProgRiego.water_before_1)
    byteList.insert(3, ProgRiego.water_before_2, )
    byteList.insert(4, ProgRiego.water_after_1)
    byteList.insert(5, ProgRiego.water_after_2)
    byteList.insert(6, ProgRiego.time_between_1)
    byteList.insert(7, ProgRiego.time_between_2)
    byteList.insert(8, ProgRiego.time_start_1)
    byteList.insert(9, ProgRiego.time_start_2)
    byteList.insert(10, ProgRiego.units)
    byteList.insert(11, ProgRiego.fertilization_program)
    byteList.insert(12, ProgRiego.kicks)
    byteList.insert(13, ProgRiego.condition_program)
    byteList.insert(14, int(RegistrosDays[0]))  # Domingo
    byteList.insert(15, int(RegistrosDays[1]))  # Lunes
    Add = BASE_PROGRIEGO + (pr - 1) * 32
    write_registers(Add, 8, byteList)
    byteList = []
    byteList.insert(0, int(RegistrosDays[2]))  # Martes
    byteList.insert(1, int(RegistrosDays[3]))  # Miercoles
    byteList.insert(2, int(RegistrosDays[4]))  # Jueves
    byteList.insert(3, int(RegistrosDays[5]))  # Viernes
    byteList.insert(4, int(RegistrosDays[6]))  # Sabado
    for counterRegister in range(5, 5+len(RegistrosValvulas)):
        byteList.insert(counterRegister, int(RegistrosValvulas[counterRegister-5]))
    byteList.append(0)  # Campo Reservado
    Add = BASE_PROGRIEGO + (pr - 1) * 32 + 16
    write_registers(Add, 8, byteList)
    # send to ram
    if ProgRiego.status == 3:
        byteList = read_registers(BASE_PROGRIEGO_STATE_RAM, 1)
        byteList[0] = ProgRiego.program
        write_registers(BASE_PROGRIEGO_STATE_RAM, 1, byteList)
    elif ProgRiego.status >= 0:
        byteList = read_registers(BASE_PROGRIEGO_STATE+pr-1, 1)
        byteList[0] = ProgRiego.status
        write_registers(BASE_PROGRIEGO_STATE+pr-1, 1, byteList)
    ProgRiego.status = -1

def write_controller_config_alarms():
    ConfigAl = cs.alarm_config
    byteList = []
    byteList.append(ConfigAl.delay_secs_if_diff_ec_more_1)
    byteList.append(ConfigAl.delay_secs_if_diff_ec_more_05)
    byteList.insert(2, ConfigAl.delay_secs_if_diff_ec_more_03)
    byteList.insert(3, ConfigAl.coefficient_correction_ec_more_1)
    byteList.insert(4, ConfigAl.coefficient_correction_ec_more_05)
    byteList.insert(5, ConfigAl.coefficient_correction_ec_more_03)
    byteList.insert(6, ConfigAl.delay_secs_if_diff_ph_more_1)
    byteList.insert(7, ConfigAl.delay_secs_if_diff_ph_more_05)
    byteList.insert(8, ConfigAl.delay_secs_if_diff_ph_more_03)
    byteList.insert(9, ConfigAl.coefficient_correction_ph_more_1)
    byteList.insert(10, ConfigAl.coefficient_correction_ph_more_05)
    byteList.insert(11, ConfigAl.coefficient_correction_ph_more_03)
    write_registers(BASE_CONFIGECPHPARAMS, 6, byteList)
    byteList = []
    byteList.insert(0, ConfigAl.secs_first_ph_correction)
    byteList.insert(1, ConfigAl.deviation_warning_max_error_flow)
    byteList.insert(2, ConfigAl.delay_alarms_ec_ph_secs)
    byteList.insert(3, ConfigAl.delay_alarm_ph_dangerous_secs)
    byteList.insert(4, ConfigAl.delay_alarm_ec_dangerous_secs)
    byteList.insert(5, ConfigAl.delay_alarm_high_pressure_kg)
    byteList.insert(6, ConfigAl.delay_alarm_low_pressure_secs)
    byteList.insert(7, ConfigAl.delay_alarm_flow_secs)
    byteList.insert(8, int(ConfigAl.max_diff_warning_error_ec * 10))
    byteList.insert(9, int(ConfigAl.max_diff_warning_error_ph * 10))
    byteList.insert(10, int(ConfigAl.max_deviation_under_ph * 10))
    byteList.insert(11, int(ConfigAl.max_deviation_over_ec * 10))
    byteList.insert(12, int(ConfigAl.level_alarm_high_pressure_kg * 10))
    byteList.insert(13, int(ConfigAl.level_alarm_low_pressure_kg * 10))
    write_registers(BASE_CONFIGALARMAS - 1, 7, byteList)
    byteList = []
    byteList.insert(0, 0)
    byteList.insert(1, ConfigAl.function_alarm_fertilizer_discontinued)
    byteList.insert(3, ConfigAl.function_alarm_ec_ph_dangerous)
    byteList.insert(3, ConfigAl.function_alarm_high_pressure)
    byteList.insert(4, ConfigAl.function_alarm_dangerous_flow)
    byteList.insert(5, ConfigAl.function_alarm_no_fertilization)
    byteList.insert(6, ConfigAl.function_alarm_no_water)
    byteList.insert(7, ConfigAl.pulses_fertilizer_no_control)
    byteList.insert(8, ConfigAl.pulses_needs_fertilizer)
    byteList.insert(9, ConfigAl.max_seconds_between_water_pulses)
    byteList.insert(10, ConfigAl.over_dangerous_flow_percentage)
    # Tiempo Anti Picos
    byteList.insert(11, 10)
    write_registers(BASE_CONFIGALARMAS + 13, 6, byteList)

def write_controller_solape():
    solape = cs.solape
    byteList = []
    import math
    flow = solape.flow.split(',')
    flow = [math.floor(float(i)) for i in flow]
    solapeNew = solape.solape.split(',')
    solapeNew = [int(i) for i in solapeNew]
    time = solape.time.split(',')
    time = [float(i) for i in time]
    i = 0
    while i < len(flow):
        byteList.append(flow[i])
        i += 1
    i = 0
    while i < len(solapeNew):
        byteList.append(solapeNew[i])
        i += 1
    i = 0
    counter = 0
    while counter < 20:
        write_registers(BASE_SOLAPE + counter*8, 4, byteList[counter*8:counter*8+8])
        counter += 1
    byteListFix = []
    i = 0
    while i < 10:
        import math
        t = time[i]
        if t >= 0.0:
            t = t * 100
            byteListFix.append(math.floor(t / 256))
            byteListFix.append(math.floor(t % 256))
        else:
            t = 65536 - abs(t * 100)
            byteListFix.append(math.floor(t / 256))
            byteListFix.append(math.floor(t % 256))
        i += 1
    write_registers(BASE_SOLAPE_MMSS, 5, byteListFix[0:10])
    write_registers(BASE_SOLAPE_MMSS+10, 5, byteListFix[10:20])

def write_controller_backflush():
    backflush = cs.back_flushing
    byteList = []
    byteList.append(int(backflush.difference_backflush_kg*10))
    byteList.append(backflush.time_between_flushing_hours)
    byteList.append(backflush.time_between_flushing_minutes)
    byteList.append(backflush.time_between_station_min)
    byteList.append(backflush.time_between_station_sec)
    byteList.append(backflush.pause_between_filtering_secs)
    byteList.append(backflush.amount_of_filters)
    byteList.append(backflush.delay_differential_pressure)
    byteList.append(backflush.wait_after_sustain)
    byteList.append(backflush.times_wash_before_pd_alarm)
    write_registers(BASE_ADDRETROLAVADO, 5, byteList)

def set_bit(v, index, x):
  """Set the index:th bit of v to 1 if x is truthy, else to 0, and return the new value."""
  mask = 1 << index
  v &= ~mask
  if x:
    v |= mask
  return v

def write_backflush_button():
    # buttons stop wash (first byte) y wash now (segundo byte)
    # BASE_BUTTON_WASH_NOW = 0x37D
    byteList = read_registers(BASE_BUTTON_WASH_NOW, 1)
    if cs.other.button_backwash_cancel:
        byteList[0] = 0
        byteList[1] = 1
    elif cs.other.button_backwash_now:
        byteList[0] = 1
        byteList[1] = 0
    cs.other.button_backwash_cancel = 0
    cs.other.button_backwash_now = 0
    write_registers(BASE_BUTTON_WASH_NOW, 1, byteList)

def send_server():
    global write_backflush
    global write_other
    global write_ConfigAl
    global write_solape
    global write_configIO
    global write_irrProg
    global write_fertProg
    global write_ConfIny
    if write_backflush and not cs.back_flushing.iszero():
        send_backflush()
    if write_ConfigAl and not cs.alarm_config.iszero():
        send_set_config_alarms()
    if write_solape and not cs.solape.iszero():
        send_solape()
    if write_configIO and not cs.config_io.iszero():
        send_config_input_output()
    if write_other and not cs.other.iszero():
        send_other()
    for key in cs.allIrrigation:
        if write_irrProg[key - 1] == True and not cs.allIrrigation[key].iszero():
            send_set_irrigation(key)
            send_set_irrigation_state_status(key, False)
    for key in cs.allInyection:
        if write_ConfIny[key - 1] == True and not cs.allInyection[key].iszero():
            send_set_inyection(key)
    for key in cs.allFertilization:
        if write_fertProg[key - 1] == True and not cs.allFertilization[key].iszero():
            send_set_fertilization(key)
    write_backflush = False
    write_other = False
    write_ConfigAl = False
    write_solape = False
    write_configIO = False
    write_irrProg = [False] * 50
    write_fertProg = [False] * 20
    write_ConfIny = [False] * 8

def send_set_fertilization(pf):
    if pf in cs.allFertilization:
        fert = cs.allFertilization[pf]
        response = requests.get(
            URL_SERVER + 'requests?set_fertilization&username=' + USERNAME + '&password=' + PASSWORD +
            "&program=" + str(fert.program) + "&who=1" + "&value_1=" + str(fert.values_1) +
            "&value_2=" + str(fert.values_2) + "&value_3=" + str(fert.values_3) + "&value_4=" + str(fert.values_4) +
            "&value_5=" + str(fert.values_5) + "&value_6=" + str(fert.values_6) + "&value_7=" + str(fert.values_7) +
            "&value_8=" + str(fert.values_8) + "&ec=" + str(fert.ec) + "&ph=" + str(fert.ph))
        dataJson = response.json()
        return (dataJson)

def send_set_irrigation(irrId):
    if irrId in cs.allIrrigation:
        irr = cs.allIrrigation[irrId]
        response = requests.get(URL_SERVER + 'requests?set_irrigation&username=' + USERNAME + '&password=' + PASSWORD +
            "&program=" + str(irr.program) + "&who=1"
            "&units=" + str(irr.units) + "&water_before_1=" + str(irr.water_before_1) +
            "&water_before_2=" + str(irr.water_before_2) + "&water_after_1=" +
            str(irr.water_after_1) + "&water_after_2=" + str(irr.water_after_2) +
            "&water_total_1=" + str(irr.water_total_1) + "&water_total_2=" + str(irr.water_total_2) +
            "&kicks=" + str(irr.kicks) + "&fertilization_program=" + str(irr.fertilization_program) +
            "&condition_program=" + str(irr.condition_program) + "&time_start_1=" + str(irr.time_start_1) +
            "&time_start_2=" + str(irr.time_start_2) + "&time_between_1=" + str(irr.time_between_1) +
            "&time_between_2=" + str(irr.time_between_2) + "&valves=" + str(irr.valves) + "&days=" + str(irr.days))
        dataJson = response.json()
        return (dataJson)

def send_set_irrigation_state_status(irrId, shouldReset):
    if irrId in cs.allIrrigation:
        irr = cs.allIrrigation[irrId]
        irr.status = -2 if shouldReset else -1
        response = requests.get(URL_SERVER + 'requests?set_irrigation_state_status&username=' + USERNAME + '&password=' + PASSWORD +
            "&program=" + str(irr.program) + "&who=1&state=" + str(irr.state) + "&status=" + str(irr.status))
        dataJson = response.json()
        return (dataJson)

def send_set_inyection(inyId):
    if inyId in cs.allInyection:
        iny = cs.allInyection[inyId]
        response = requests.get(URL_SERVER + 'requests?set_inyector&username=' + USERNAME + '&password=' + PASSWORD +
            "&program=" + str(iny.program) + "&who=1&flow=" + str(iny.flow) +
            "&time_on=" + str(iny.time_on) + "&litres_pulse=" + str(iny.litres_pulse) + "&max_deviation=" + str(iny.max_deviation) +
            "&simulator=" + str(iny.simulator) + "&function=" + str(iny.function))
        dataJson = response.json()
        return (dataJson)

def send_set_config_alarms():
    cA = cs.alarm_config
    response = requests.get(URL_SERVER + 'requests?set_config_alarms&username=' + USERNAME + '&password=' + PASSWORD +
        "&who=1&deviation_warning_max_error_flow=" + str(cA.deviation_warning_max_error_flow) +
        "&function_alarm_ec_ph_dangerous=" + str(cA.function_alarm_ec_ph_dangerous) +
        "&delay_alarms_ec_ph_secs=" + str(cA.delay_alarms_ec_ph_secs) +
        "&delay_alarm_ph_dangerous_secs=" + str(cA.delay_alarm_ph_dangerous_secs) +
        "&delay_alarm_ec_dangerous_secs=" + str(cA.delay_alarm_ec_dangerous_secs) +
        "&delay_alarm_high_pressure_kg=" + str(cA.delay_alarm_high_pressure_kg) +
        "&delay_alarm_low_pressure_secs=" + str(cA.delay_alarm_low_pressure_secs) +
        "&delay_alarm_flow_secs=" + str(cA.delay_alarm_flow_secs) +
        "&max_diff_warning_error_ec=" + str(cA.max_diff_warning_error_ec) +
        "&max_diff_warning_error_ph=" + str(cA.max_diff_warning_error_ph) +
        "&max_deviation_under_ph=" + str(cA.max_deviation_under_ph) +
        "&max_deviation_over_ec=" + str(cA.max_deviation_over_ec) +
        "&level_alarm_high_pressure_kg=" + str(cA.level_alarm_high_pressure_kg) +
        "&level_alarm_low_pressure_kg=" + str(cA.level_alarm_low_pressure_kg) +
        "&function_alarm_fertilizer_discontinued=" + str(cA.function_alarm_fertilizer_discontinued) +
        "&function_alarm_high_pressure=" + str(cA.function_alarm_high_pressure) +
        "&function_alarm_dangerous_flow=" + str(cA.function_alarm_dangerous_flow) +
        "&function_alarm_no_fertilization=" + str(cA.function_alarm_no_fertilization) +
        "&function_alarm_no_water=" + str(cA.function_alarm_no_water) +
        "&pulses_fertilizer_no_control=" + str(cA.pulses_fertilizer_no_control) +
        "&pulses_needs_fertilizer=" + str(cA.pulses_needs_fertilizer) +
        "&max_seconds_between_water_pulses=" + str(cA.max_seconds_between_water_pulses) +
        "&over_dangerous_flow_percentage=" + str(cA.over_dangerous_flow_percentage) +
        "&delay_secs_if_diff_ec_more_1=" + str(cA.delay_secs_if_diff_ec_more_1) +
        "&delay_secs_if_diff_ec_more_05=" + str(cA.delay_secs_if_diff_ec_more_05) +
        "&delay_secs_if_diff_ec_more_03=" + str(cA.delay_secs_if_diff_ec_more_03) +
        "&coefficient_correction_ec_more_1=" + str(cA.coefficient_correction_ec_more_1) +
        "&coefficient_correction_ec_more_05=" + str(cA.coefficient_correction_ec_more_05) +
        "&coefficient_correction_ec_more_03=" + str(cA.coefficient_correction_ec_more_03) +
        "&delay_secs_if_diff_ph_more_1=" + str(cA.delay_secs_if_diff_ph_more_1) +
        "&delay_secs_if_diff_ph_more_05=" + str(cA.delay_secs_if_diff_ph_more_05) +
        "&delay_secs_if_diff_ph_more_03=" + str(cA.delay_secs_if_diff_ph_more_03) +
        "&coefficient_correction_ph_more_1=" + str(cA.coefficient_correction_ph_more_1) +
        "&coefficient_correction_ph_more_05=" + str(cA.coefficient_correction_ph_more_05) +
        "&coefficient_correction_ph_more_03=" + str(cA.coefficient_correction_ph_more_03) +
        "&secs_first_ec_correction=" + str(cA.secs_first_ec_correction) +
        "&secs_first_ph_correction=" + str(cA.secs_first_ph_correction))
    dataJson = response.json()
    return (dataJson)

def send_config_input_output():
    cIO = cs.config_io
    cIO.analog_input_5 = "0,0,0,0"
    response = requests.get(URL_SERVER + 'requests?set_io_config&username=' + USERNAME + '&password=' + PASSWORD +
        "&who=1&inyection=" + str(cIO.inyection) + "&filters=" + str(cIO.filters) +
        "&actuators=" + str(cIO.actuators) + "&valves1to16=" + str(cIO.valves1to16) +
        "&valves17to32=" + str(cIO.valves17to32) + "&valves33to48=" + str(cIO.valves33to48) +
        "&valves49to64=" + str(cIO.valves49to64) + "&valves65to80=" + str(cIO.valves65to80) +
        "&analog_input_1=" + str(cIO.analog_input_1) + "&analog_input_2=" + str(cIO.analog_input_2) +
        "&analog_input_3=" + str(cIO.analog_input_3) + "&analog_input_4=" + str(cIO.analog_input_4) +
        "&analog_input_5=" + str(cIO.analog_input_5))
    dataJson = response.json()
    return dataJson
  
def send_backflush():
    bf = cs.back_flushing
    response = requests.get(URL_SERVER + 'requests?set_backflushing_config&username=' + USERNAME + '&password=' + PASSWORD +
        '&who=1&time_between_station_sec=' + str(bf.time_between_station_sec) +
        '&pause_between_filtering_secs=' + str(bf.pause_between_filtering_secs) +
        '&amount_of_filters=' + str(bf.amount_of_filters) +
        '&difference_backflush_kg=' + str(bf.difference_backflush_kg) +
        '&delay_differential_pressure=' + str(bf.delay_differential_pressure) +
        '&wait_after_sustain=' + str(bf.wait_after_sustain) +
        '&times_wash_before_pd_alarm=' + str(bf.times_wash_before_pd_alarm) +
        '&time_between_flushing_hours=' + str(bf.time_between_flushing_hours) +
        '&time_between_flushing_minutes=' + str(bf.time_between_flushing_minutes))
    dataJson = response.json()
    return dataJson

def send_solape():
    solape = cs.solape
    response = requests.get(URL_SERVER + 'requests?set_solape_config&username=' + USERNAME + '&password=' + PASSWORD + '&who=1&solape=' + solape.solape + '&time=' + solape.time + '&flow=' + solape.flow)
    dataJson = response.json()
    return dataJson

def send_backwash_buttons():
    response = requests.get(URL_SERVER + 'requests?set_backwash_buttons' +
    '&username=' + USERNAME + '&password=' + PASSWORD + '&who=1' +
    '&button_backwash_now=' + str(cs.other.button_backwash_now) +
    '&button_backwash_cancel=' + str(cs.other.button_backwash_cancel))
    dataJson = response.json()
    return dataJson

def send_other():
    other = cs.other
    response = requests.get(URL_SERVER + 'requests?set_other_config&username=' + USERNAME + '&password=' + PASSWORD +
        '&who=1&booster_pump=' + str(other.booster_pump) +
        '&flow_meter_1=' + str(other.flow_meter_1) +
        '&flow_meter_2=' + str(other.flow_meter_2) +
        '&time_restart_program_1=' + str(other.time_restart_program_1) +
        '&time_restart_program_2=' + str(other.time_restart_program_2) +
        '&blower_1=' + str(other.blower_1) +
        '&blower_2=' + str(other.blower_2) +
        '&toff_inyector=1' +
        '&manual_irrigation_units=' + str(other.manual_irrigation_units) +
        '&manual_irrigation_water_1=' + str(other.manual_irrigation_water_1) +
        '&manual_irrigation_water_2=' + str(other.manual_irrigation_water_2) +
        '&manual_irrigation_program=' + str(other.manual_irrigation_program))
    dataJson = response.json()
    return dataJson

def send_alarm():
    read_from_alarms()
    alarm = cs.alarm
    response = requests.get(URL_SERVER + 'requests?set_alarms&username=' + USERNAME + '&password=' + PASSWORD +
        '&fertilization_deficit=' + alarm.fertilization_deficit +
        '&fertilization_desc=' + alarm.fertilization_desc +
        '&ec_error=' + str(alarm.ec_error) +
        '&ph_error=' + str(alarm.ph_error) +
        '&ec_danger=' + str(alarm.ec_danger) +
        '&ph_danger=' + str(alarm.ph_danger) +
        '&low_pressure=' + str(alarm.low_pressure) +
        '&high_pressure=' + str(alarm.high_pressure) +
        '&flow_error=' + str(alarm.flow_error) +
        '&no_water=' + str(alarm.no_water) +
        '&dangerous_flow=' + str(alarm.dangerous_flow) +
        '&irrigation_out_of_controls=' + str(alarm.irrigation_out_of_controls))
    dataJson = response.json()
    return dataJson

def send_power_buttons():
    read_from_alarms()
    alarm = cs.alarm
    response = requests.get(URL_SERVER + 'requests?set_power_buttons&username=' + USERNAME + '&password=' + PASSWORD + '&who=1&stop_button=0&start_button=0')
    dataJson = response.json()
    return dataJson

def read_from_terminal_stats():
    termStats = TerminalStats()
    byteList = read_registers(BASE_FERT, 1)
    termStats.fertilization_program = byteList[0]
    byteList = read_registers(BASE_NEXT_PROG, 1)
    termStats.next_irrigation_program = byteList[0]
    byteList = read_registers(BASE_IRRIGATION, 5)
    termStats.irrigation_program = byteList[0]
    termStats.irrigation_1 = byteList[1]
    termStats.irrigation_2 = byteList[2]
    termStats.preirrigation_1 = byteList[3]
    termStats.preirrigation_2 = byteList[4]
    termStats.postirrigation_1 = byteList[6]
    termStats.postirrigation_2 = byteList[7]
    termStats.units = byteList[8]
    byteList = read_registers(BASE_M3, 2)
    termStats.cubic_meters = float(byteList[0])/10
    byteList = read_registers(BASE_IRRIGATION_TIME, 2)
    termStats.irrigation_time_1 = byteList[0]
    termStats.irrigation_time_2 = byteList[1]
    termStats.irrigation_time_3 = byteList[2]
    byteList = read_registers(BASE_TOTAL_IRRIGATION, 2)
    test = byteList[0] * 256 + byteList[1]
    test += float(byteList[2])/100
    termStats.cubic_meters = test
    byteList = read_registers(BASE_MEASURED_FLOW, 2)
    test = byteList[0] * 256 + byteList[1]
    test += float(byteList[2])/100
    termStats.flow_measured_m3_h = test
    byteList = read_registers(BASE_C_PROG, 1)
    termStats.c_prog = byteList[1]
    byteList = read_registers(BASE_P1_P2, 1)
    termStats.p1 = float(byteList[0])/10
    termStats.p2 = float(byteList[1])/10
    byteList = read_registers(BASE_EC_PH_MEASURED, 1)
    termStats.ec_measured = float(byteList[0])/10
    termStats.ph_measured = float(byteList[1])/10
    byteList = read_registers(BASE_EC_PH_ASKED, 1)
    termStats.ph_asked = float(byteList[0])/10
    termStats.ec_asked = float(byteList[1])/10
    byteList = read_registers(BASE_EC_PH_AVERAGE, 1)
    termStats.ph_average = float(byteList[0])/10
    termStats.ec_average = float(byteList[1])/10
    byteList = read_registers(BASE_VALVES_STATS, 5)
    termStats.valves = []
    for i in byteList:
        y = 0
        while y < 8:
            termStats.valves.append(is_set(i, y))
            y += 1
    termStats.valves = ','.join(str(e) for e in termStats.valves)

    termStats.filters = FilterStats()
    byteList = read_registers(BASE_FILTERS_RAM, 1)
    for i in range(0, 8):
        termStats.filters.filters.append(is_set(byteList[0], i))
    termStats.filters.filters = ','.join(map(str, termStats.filters.filters))
    termStats.filters.sustain_valve = is_set(byteList[1], 4)
    byteList = read_registers(BASE_FILTER_CLEANING_MOTIVE, 1)
    termStats.filters.backwash_reason = byteList[0]
    byteList = read_registers(BASE_NO_WASHER, 1)
    termStats.filters.backwash_state = is_set(byteList[0], 0)
    byteList = read_registers(BASE_NEXT_WASHER, 1)
    termStats.filters.next_backwash_hour = byteList[0] % 100
    termStats.filters.next_backwash_min = byteList[1] % 100

    byteList = []
    byteList += read_registers(BASE_INYECTOR_STATS_1_2, 8)
    byteList += read_registers(BASE_INYECTOR_STATS_1_2+16, 8)
    byteList += read_registers(BASE_INYECTOR_STATS_3, 6)
    byteList += read_registers(BASE_INYECTOR_STATS_3+12, 6)
    byteList += read_registers(BASE_INYECTOR_STATS_4, 8)
    byteList += read_registers(BASE_INYECTOR_STATS_5, 6)
    byteList += read_registers(BASE_INYECTOR_STATS_5+12, 6)
    termStats.inyectors = []
    i, f = 0, 0
    while f < 8:
        iny = InyectorStats()
        iny.inyector = f + 1
        helper = byteList[0 +f*2 ] * 256 + byteList[1 + f*2]
        iny.prop_required = helper
        helper = byteList[16 + f*2] * 256 + byteList[17 + f*2]
        iny.prop_required_ec_ph = helper
        helper = byteList[32 + f*3] * 256 + byteList[33 + f*3]
        helper += float(byteList[34 + f*3])/100
        iny.required_flow = helper
        helper = byteList[56 + f*2] * 256 + byteList[57 + f*2]
        iny.required_volume = float(helper)/10
        helper = byteList[72 + f*3] * 256 + byteList[73 + f*3]
        helper += float(byteList[74 + f*3])/100
        iny.total_inyected = helper
        termStats.inyectors.append(iny)
        i = i + 12
        f = f + 1
    termStats.actuators = ActuatorStats()
    byteList = read_registers(BASE_ACTUATORS_RAM, 1)
    termStats.actuators.irrigation_pump = is_set(byteList[0], 0)
    termStats.actuators.fertilization_pump = is_set(byteList[0], 1)
    termStats.actuators.blender = is_set(byteList[0], 2)
    termStats.actuators.alarm = is_set(byteList[0], 3)
    byteList = read_registers(BASE_ACTUATORS_INYECTOR_RAM, 1)
    inyectors = []
    for i in range(0, 8):
        inyectors.append(is_set(byteList[0], i))
    termStats.actuators.inyectors = ','.join(map(str, inyectors))
    return termStats

def read_from_controller_irr_info():
    to_return = []
    for i in range(50):
        byteList = [0, i+1]
        write_registers(BASE_IRR_INFO, 1, byteList)
        write_registers(BASE_IRR_INFO_SEND_KEY, 2, BASE_KEYS_INFO)

        import time
        isZero = False
        while isZero is not True:
            byteList = read_registers(BASE_IRR_INFO_SEND_KEY, 2)
            if all(v == 0 for v in byteList):
                isZero = True
                
        infoProg = InfoIrrigation()
        infoProg.prog = i+1
        infoProg.inyectors = []
        byteList = read_registers(BASE_IRR_INFO_KICKS, 3)
        infoProg.kicks = byteList[0]
        infoProg.total_m3 = byteList[1]*256+byteList[2]
        infoProg.total_hh = byteList[3]
        infoProg.total_mm = byteList[4]
        byteList = read_registers(BASE_IRR_INFO_HH_MM_ULTIMO_RIEGO, 1)
        infoProg.next_irr_hh = byteList[0]
        infoProg.next_irr_mm = byteList[1]
        byteList = read_registers(BASE_IRR_INFO_PH_EC_PROMEDIO, 1)
        infoProg.ec_avg = byteList[1]/10
        infoProg.ph_avg = byteList[0]/10
        byteList = read_registers(BASE_IRR_INFO_INYECTORS, 6)
        byteList += read_registers(BASE_IRR_INFO_INYECTORS+12, 6)
        for i in range(0, 8):
            total_inyected = (byteList[0 + 3*i] * 256 + byteList[1 + 3*i] % 256) + byteList[2 + 3*i] / 100
            infoProg.inyectors.append(total_inyected)
        to_return.append(infoProg)
    return to_return

def send_terminal_stats():
    stats = read_from_terminal_stats()
    if stats != None:
        response = requests.get(URL_SERVER + 'requests?set_stats&username=' + USERNAME + '&password=' + PASSWORD +
            '&irrigation_program=' + str(stats.irrigation_program) +
            '&fertilization_program=' + str(stats.fertilization_program) +
            '&next_irrigation_program=' + str(stats.next_irrigation_program) +
            '&irrigation_1=' + str(stats.irrigation_1) +
            '&irrigation_2=' + str(stats.irrigation_2) +
            '&preirrigation_1=' + str(stats.preirrigation_1) +
            '&preirrigation_2=' + str(stats.preirrigation_2) +
            '&postirrigation_1=' + str(stats.postirrigation_1) +
            '&postirrigation_2=' + str(stats.postirrigation_2) +
            '&units=' + str(stats.units) +
            '&irrigation_time_1=' + str(stats.irrigation_time_1) +
            '&irrigation_time_2=' + str(stats.irrigation_time_2) +
            '&irrigation_time_3=' + str(stats.irrigation_time_3) +
            '&cubic_meters=' + str(stats.cubic_meters) +
            '&irrigation_before_suspend_1=' + str(stats.irrigation_before_suspend_1) +
            '&irrigation_before_suspend_2=' + str(stats.irrigation_before_suspend_2) +
            '&flow_measured_m3_h=' + str(stats.flow_measured_m3_h) +
            '&p1_kg=' + str(stats.p1) +
            '&p2_kg=' + str(stats.p2) +
            '&condition_program=' + str(stats.c_prog) +
            '&ec_asked=' + str(stats.ec_asked) +
            '&ph_asked=' + str(stats.ph_asked) +
            '&ec_medium=' + str(stats.ec_measured) +
            '&ph_medium=' + str(stats.ph_measured) +
            '&ec_average=' + str(stats.ec_average) +
            '&ph_average=' + str(stats.ph_average) +
            '&valves=' + str(stats.valves))
        dataJson = response.json()
        response = requests.get(URL_SERVER + 'requests?set_stats_actuators&username=' + USERNAME + '&password=' + PASSWORD +
            '&irrigation_pump=' + str(stats.actuators.irrigation_pump) +
            '&fertilization_pump=' + str(stats.actuators.fertilization_pump) +
            '&blender=' + str(stats.actuators.blender) +
            '&alarm=' + str(stats.actuators.alarm) +
            '&inyectors=' + stats.actuators.inyectors)
        dataJson = response.json()
        response = requests.get(URL_SERVER + 'requests?set_filters_stats&username=' + USERNAME + '&password=' + PASSWORD +
            '&filters=' + stats.filters.filters +
            '&sustain_valve=' + str(stats.filters.sustain_valve) +
            '&backwash_state=' + str(stats.filters.backwash_state) +
            '&backwash_reason=' + str(stats.filters.backwash_reason) +
            '&next_backwash_min=' + str(stats.filters.next_backwash_min) +
            '&next_backwash_hour=' + str(stats.filters.next_backwash_hour) +
            '&backwash_manual=-1&backwash_manual_now=-1')
        dataJson = response.json()
        for i in stats.inyectors:
            response = requests.get(URL_SERVER + 'requests?set_inyector_stats&username=' + USERNAME + '&password=' + PASSWORD +
                '&program=' + str(i.inyector) +
                '&prop_required=' + str(i.prop_required) +
                '&prop_required_ec_ph=' + str(i.prop_required_ec_ph) +
                '&required_flow=' + str(i.required_flow) +
                '&required_volume=' + str(i.required_volume) +
                '&total_inyected=' + str(i.total_inyected))
        return dataJson

def get_total_books():
    byteList = read_registers(BASE_BOOKS_TOTAL, 1)
    return byteList[0] * 256 + byteList[1]

def get_total_books_server():
    response = requests.get(
        URL_SERVER +
        'requests?get_book_count&username=' +
        USERNAME +
        '&password=' +
        PASSWORD)
    dataJson = response.json()
    return dataJson['count']

def clear_all_books_server():
    response = requests.get(
        URL_SERVER +
        'requests?clear_books&username=' +
        USERNAME +
        '&password=' +
        PASSWORD)
    dataJson = response.json()
    return dataJson['error']

def send_books(book):
    inyectors = ','.join(str(e) for e in book.inyectors)
    response = requests.get(
        URL_SERVER +
        'requests?set_books&username=' +
        USERNAME +
        '&password=' +
        PASSWORD +
        "&book_id=" + str(book.book) +
        "&date_year=" + str(book.date_year) +
        "&date_month=" + str(book.date_month) +
        "&date_day=" + str(book.date_day) +
        "&start_time_seconds=" + str(book.date_time_seconds) +
        "&total_irrigation_seconds=" + str(book.irrigation_time_seconds) +
        "&irrigation_m3=" + str(book.irrigation_m3) +
        "&ec_avg=" + str(book.ec_avg) +
        "&ph_avg=" + str(book.ph_avg) +
        "&fertilization_program=" + str(book.fert_prog) +
        "&irrigation_program=" + str(book.irr_prog) +
        "&inyectors=" + inyectors)
    dataJson = response.json()
    return dataJson['error']

def get_book(book):
    byteList = [int((book-1)*64/256), (book-1)*64%256]
    write_registers(BASE_BOOKS_NUMBER, 1, byteList)
    write_registers(BASE_BOOKS_SEND_KEY, 2, BASE_KEYS_BOOK)

    import time
    isZero = False
    while isZero is not True:
        byteList = read_registers(BASE_BOOKS_SEND_KEY, 2)
        if all(v == 0 for v in byteList):
            isZero = True

    bookrecord = BookRecord()
    bookrecord.book = book
    byteList = read_registers(BASE_BOOKS_DATE, 5)
    bookrecord.date_day = byteList[1]
    bookrecord.date_month = byteList[2]
    bookrecord.date_year = byteList[3]
    bookrecord.date_time_seconds = byteList[4]*60*60 + byteList[5]*60 + byteList[6]

    byteList = read_registers(BASE_BOOKS_TOTAL_QTY, 2)
    bookrecord.irrigation_m3 = byteList[0]*256 + byteList[1] + byteList[2]/100
    byteList = read_registers(BASE_BOOKS_TOTAL_TIME, 2)
    bookrecord.irrigation_time_seconds = byteList[0]*60*60 + byteList[1]*60 + byteList[2]
    byteList = read_registers(BASE_BOOKS_IRR_FERT, 1)
    bookrecord.irr_prog = byteList[0]
    bookrecord.fert_prog = byteList[1]
    byteList = read_registers(BASE_BOOKS_PH_EC_AVG, 1)
    bookrecord.ph_avg = byteList[0]
    bookrecord.ec_avg = byteList[1]

    byteList = read_registers(BASE_BOOKS_INYECTORS, 6)
    byteList += read_registers(BASE_BOOKS_INYECTORS+12, 6)
    bookrecord.inyectors = []
    for i in range(0, 8):
        total_inyected = (byteList[0 + 3*i] * 256 + byteList[1 + 3*i] % 256) + byteList[2 + 3*i] / 100
        bookrecord.inyectors.append(total_inyected)
    
    return bookrecord

def on_controller_modifier():
    data = fetch_json()
    cs.load_from_json(data)
    read_from_backflushing()
    read_from_solape()
    read_from_controller_config_alarms()
    read_from_controller_input_output()
    read_from_other_configs()
    for i in range(0, TOTAL_FERT):
        read_from_controller_fertilization(i + 1)
    for i in range(0, TOTAL_IRR):
        read_from_controller_irrigation(i + 1)
    for i in range(0, TOTAL_INY):
        read_from_controller_inyectors(i + 1)

def calculate_crc(listCRC):
    i = 0
    rot = 0
    result = 0xFFFF
    while (i < len(listCRC)):
        result = result ^ listCRC[i]
        while (rot < 8):
            if (result & 0x0001) == 1:
                result = result >> 1
                result = result ^ 0xA001
            else:
                result = result >> 1
            rot = rot + 1
        rot = 0
        i = i + 1
    CRCH = int(result / 256)
    CRCL = result % 256
    listCRC = [CRCL, CRCH]
    return listCRC

def bytes2integer(stream):
    bytes_in = []
    for b in stream:
        bytes_in.append(int(hex(b), 16))
    return bytes_in

# init
correctLogin = False
cs = ControllerState()
if os.path.isfile(FILEPATH_SAVE):
    cs = ControllerState.load_from_file(FILEPATH_SAVE)
tickCounter, tickCounterErr = 0, 0
statsCounter = 0

try:
    os.remove("/home/pi/fertiriego.log")
except OSError:
    pass


logger = logging.getLogger()
handler = RotatingFileHandler("/home/pi/fertiriego.log",maxBytes=1024*1024*400,backupCount=0)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

def main_loop():
    global correctLogin, tickCounter, tickCounterErr, cs, statsCounter
    if not correctLogin:
        correctLogin = check_login()
        if correctLogin:
            logger.info("login ok")
        else:
            logger.info("login error")                           
    else:
        # mandar manual irr y estado de prog cada 6 updates, aprox 12s
        if statsCounter % 10 == 1:
            read_from_other_configs()
            global write_other
            if write_other:
                send_other()
                write_other = False
        # mandar cada 2 updates, aprox 4s
        if statsCounter == 0:
            for prog in cs.allIrrigation:
                byteList = read_registers(BASE_PROGRIEGO_STATE+prog-1, 1)
                old_state = cs.allIrrigation[prog].state
                cs.allIrrigation[prog].state = byteList[0]
                send_set_irrigation_state_status(prog)
        if statsCounter % 10 == 1:
            for prog in cs.allIrrigation:
                byteList = read_registers(BASE_PROGRIEGO_STATE+prog-1, 1)
                old_state = cs.allIrrigation[prog].state
                cs.allIrrigation[prog].state = byteList[0]
                if cs.allIrrigation[prog].state != old_state:
                    send_set_irrigation_state_status(prog)
        if statsCounter % 4 == 1:
            send_terminal_stats()
            send_alarm()
            book_count = get_total_books()
            total_books_server = get_total_books_server()
            if book_count > total_books_server:
                for i in range(total_books_server+1, book_count+1 if book_count+1 <= 200 else 200):
                    b = get_book(i)
                    send_books(b)
            elif book_count == 0:
                clear_all_books_server()
        if statsCounter % 500 == 499:
            to_send = read_from_controller_irr_info()
            for irr_info in to_send:
                payload = {'username': USERNAME, 'password': PASSWORD,
                           'set_info_irr': 1, 'prog': irr_info.prog,
                           'kicks': irr_info.kicks,
                           'total_hh': irr_info.total_hh,
                           'total_mm': irr_info.total_mm,
                           'total_m3': irr_info.total_m3,
                           'next_irr_hh': irr_info.next_irr_hh,
                           'next_irr_mm': irr_info.next_irr_mm,
                           'ph_avg': irr_info.ph_avg,
                           'ec_avg': irr_info.ec_avg,
                           'inyectors': ','.join(map(str, irr_info.inyectors))}
                response = requests.get(
                    URL_SERVER +
                    'requests', payload)
                dataJson = response.json()
        # if statsCounter % 60 == 1:
        #     book_count = get_total_books()
        #     if book_count < get_total_books_server():
        #         clear_all_books_server()
        #     for i in range(1, book_count+1 if book_count+1 <= 200 else 200):
        #         b = get_book(i)
        #         send_books(b)
        statsCounter += 1
        if read_dirty():
            logger.info("modified on controller")
            on_controller_modifier()
            send_server()
            write_dirty()
        else:
            updatedbywhen = fetch_last_update()
            lastUpdate = updatedbywhen[0]
            who = updatedbywhen[1]
            logger.info(str(tickCounter) + ": " + str(updatedbywhen))
            tickCounter += 1
            if cs.last_update != int(lastUpdate) and who == 0:
                logger.info("modified on android")
                data = fetch_json()
                new_cs = ControllerState()
                new_cs.load_from_json(data)
                what = cs.what_to_upload(new_cs)
                cs = new_cs
                cs.save_to_file(FILEPATH_SAVE)
                for x in what["irrigation"]:
                    write_controller_irrigation(x)
                for x in what["irrigation"]:
                    byteList = read_registers(BASE_PROGRIEGO_STATE+x-1, 1)
                    cs.allIrrigation[x].state = byteList[0]
                    send_set_irrigation_state_status(x, True)
                for x in what["fertilization"]:
                    write_controller_fertilization(x)
                for x in what["inyection"]:
                    write_controller_inyection(x)
                if what["backflush"]:
                    write_controller_backflush()
                if what["other"]:
                    write_other_configs()
                    if cs.other.button_backwash_cancel or cs.other.button_backwash_now:
                        write_backflush_button()
                        send_backwash_buttons()
                if cs.other.start_button or cs.other.stop_button:
                    logger.info("sec " + str(cs.other.stop_button))
                    logger.info("sec " + str(cs.other.start_button))
                    #BASE_START_BUTTON = 0x1BC # setear bit 5
                    #BASE_STOP_BUTTON = 0x1DC # setear bit 6
                    if cs.other.start_button:
                        byteList = read_registers(BASE_START_BUTTON, 1)
                        byteList[0] = byteList[0] | (1<<5)
                        write_registers(BASE_START_BUTTON, 1, byteList)
                    if cs.other.stop_button:
                        byteList = read_registers(BASE_STOP_BUTTON, 1)
                        byteList[0] = byteList[0] | (1<<6)
                        write_registers(BASE_STOP_BUTTON, 1, byteList)
                    cs.other.start_button = False
                    cs.other.stop_button = False
                    send_power_buttons()
                if what["config_io"]:
                    write_controller_input_output()
                if what["alarm_config"]:
                    write_controller_config_alarms()
                if what["solape"]:
                    write_controller_solape()

if __name__ == "__main__":
    while True:
        main_loop()
        try:
            tickCounterErr = 0
        except Exception as ex:
            logger.info("exception, restarting")
            logger.exception(ex)
            tickCounterErr += 1
            if tickCounterErr >= 5:
                logger.info("exception count too high, exiting")
                exit()
        time.sleep(TIME_UPDATE)
