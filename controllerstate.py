import pickle
import os.path

def compare_dicts(first, second):
    if set(first.keys()) == set(second.keys()):
        for k in first:
            if first[k] != second[k]:
                return False
        return True
    else:
        return False

class BookRecord:
    def __init__(self):
        self.book = 0
        self.date_year = 0
        self.date_month = 0
        self.date_day = 0
        self.date_time_seconds = 0
        self.irrigation_time_seconds = 0
        self.irrigation_m3 = 0
        self.ec_avg = 0
        self.ph_avg = 0
        self.fert_prog = 0
        self.irr_prog = 0
        self.inyectors = []

class IrrigationProgram:
    def __init__(self):
        self.program = 0
        self.units = 0
        self.water_before_1 = 0
        self.water_before_2 = 0
        self.water_after_1 = 0
        self.water_after_2 = 0
        self.water_total_1 = 0
        self.water_total_2 = 0
        self.kicks = 0
        self.fertilization_program = 0
        self.condition_program = 0
        self.time_start_1 = 0
        self.time_start_2 = 0
        self.time_between_1 = 0
        self.time_between_2 = 0
        self.status = 0
        self.state = 0
        self.days = "0,0,0,0,0,0,0"
        self.valves = ""

    def __eq__(self, other):
        return str(self.__dict__) == str(other.__dict__)
    def iszero(self):
        blank = IrrigationProgram()
        blank.program = self.program
        return self == blank


class FertilizationProgram:
    def __init__(self):
        self.program = 0
        self.values_1 = 0
        self.values_2 = 0
        self.values_3 = 0
        self.values_4 = 0
        self.values_5 = 0
        self.values_6 = 0
        self.values_7 = 0
        self.values_8 = 0
        self.ec = 0.0
        self.ph = 0.0

    def __eq__(self, other):
        return str(self.__dict__) == str(other.__dict__)
    def iszero(self):
        blank = FertilizationProgram()
        blank.program = self.program
        return self == blank


class Alarm:
    def __init__(self):
        self.fertilization_deficit = ""
        self.fertilization_desc = ""
        self.ec_error = 0
        self.ph_error = 0
        self.ec_danger = 0
        self.ph_danger = 0
        self.low_pressure = 0
        self.high_pressure = 0
        self.flow_error = 0
        self.no_water = 0
        self.dangerous_flow = 0
        self.irrigation_out_of_controls = 0

    def __eq__(self, other):
        return str(self.__dict__) == str(other.__dict__)


class InyectionProgram:
    def __init__(self):
        self.program = 0
        self.flow = 0
        self.function = 0
        self.time_on = 0
        self.litres_pulse = 0
        self.max_deviation = 0
        self.simulator = 0

    def __eq__(self, other):
        return str(self.__dict__) == str(other.__dict__)
    def iszero(self):
        blank = InyectionProgram()
        blank.program = self.program
        return self == blank


class AlarmConfig:
    def __init__(self):
        self.delay_alarm_flow_secs = 0
        self.deviation_warning_max_error_flow = 0
        self.function_alarm_no_water = 0
        self.over_dangerous_flow_percentage = 0
        self.function_alarm_dangerous_flow = 0
        self.max_seconds_between_water_pulses = 0
        self.delay_alarm_low_pressure_secs = 0
        self.level_alarm_low_pressure_kg = 0.0
        self.delay_alarm_high_pressure_kg = 0
        self.level_alarm_high_pressure_kg = 0.0
        self.function_alarm_high_pressure = 0
        self.function_alarm_no_fertilization = 0
        self.pulses_needs_fertilizer = 0
        self.function_alarm_fertilizer_discontinued = 0
        self.pulses_fertilizer_no_control = 0
        self.max_diff_warning_error_ec = 0.0
        self.max_diff_warning_error_ph = 0.0
        self.delay_alarms_ec_ph_secs = 0
        self.function_alarm_ec_ph_dangerous = 0
        self.max_deviation_over_ec = 0.0
        self.max_deviation_under_ph = 0.0
        self.delay_alarm_ec_dangerous_secs = 0
        self.delay_alarm_ph_dangerous_secs = 0
        self.delay_secs_if_diff_ec_more_1 = 0
        self.delay_secs_if_diff_ec_more_05 = 0
        self.delay_secs_if_diff_ec_more_03 = 0
        self.coefficient_correction_ec_more_1 = 0
        self.coefficient_correction_ec_more_05 = 0
        self.coefficient_correction_ec_more_03 = 0
        self.secs_first_ec_correction = 0
        self.delay_secs_if_diff_ph_more_1 = 0
        self.delay_secs_if_diff_ph_more_05 = 0
        self.delay_secs_if_diff_ph_more_03 = 0
        self.coefficient_correction_ph_more_1 = 0
        self.coefficient_correction_ph_more_05 = 0
        self.coefficient_correction_ph_more_03 = 0
        self.secs_first_ph_correction = 0

    def __eq__(self, other):
        return str(self.__dict__) == str(other.__dict__)
    def iszero(self):
        blank = AlarmConfig()
        return self == blank


class IOConfig():
    def __init__(self):
        self.inyection = "0,0,0,0,0,0,0,0"
        self.filters = "0,0,0,0,0,0,0,0"
        self.actuators = "0,0,0,0,0,0,0,0"
        self.analog_input_1 = "0,0,0,0"
        self.analog_input_2 = "0,0,0,0"
        self.analog_input_3 = "0,0,0,0"
        self.analog_input_4 = "0,0,0,0"
        self.analog_input_5 = "0,0,0,0"
        self.valves1to16 = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
        self.valves17to32 = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
        self.valves33to48 = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
        self.valves49to64 = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
        self.valves65to80 = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"

    def __eq__(self, other):
        return str(self.__dict__) == str(other.__dict__)
    def iszero(self):
        blank = IOConfig()
        return self == blank


class BackFlushing():
    def __init__(self):
        self.difference_backflush_kg = 0
        self.time_between_flushing_hours = 0
        self.time_between_flushing_minutes = 0
        self.time_between_station_min = 0
        self.time_between_station_sec = 0
        self.pause_between_filtering_secs = 0
        self.amount_of_filters = 0
        self.delay_differential_pressure = 0
        self.wait_after_sustain = 0
        self.times_wash_before_pd_alarm = 0
    def __eq__(self, other):
        return str(self.__dict__) == str(other.__dict__)
    def iszero(self):
        blank = BackFlushing()
        return self == blank


class ValveSolape():
    def __init__(self):
        self.solape = ""
        self.time = ""
        self.flow = ""

    def __eq__(self, other):
        return str(self.__dict__) == str(other.__dict__)
    def iszero(self):
        blank = ValveSolape()
        return self == blank


class OtherConfigs():
    def __init__(self):
        self.booster_pump = 0
        self.flow_meter_1 = 0
        self.flow_meter_2 = 0
        self.time_restart_program_1 = 0
        self.time_restart_program_2 = 0
        self.blower_1 = 0
        self.blower_2 = 0
        self.toff_inyector = 0
        self.manual_irrigation_units = 0
        self.manual_irrigation_water_1 = 0
        self.manual_irrigation_water_2 = 0
        self.manual_irrigation_program = 0
        self.button_backwash_now = 0
        self.button_backwash_cancel = 0
        self.start_button = 0
        self.stop_button = 0

    def __eq__(self, other):
        return str(self.__dict__) == str(other.__dict__)
    def iszero(self):
        blank = OtherConfigs()
        return self == blank

class InyectorStats:
    def __init__(self):
        self.inyector = 0
        self.prop_required = 0
        self.prop_required_ec_ph = 0
        self.required_volume = 0
        self.required_flow = 0
        self.total_inyected = 0

class ActuatorStats:
    def __init__(self):
        self.irrigation_pump = 0
        self.fertilization_pump = 0
        self.blender = 0
        self.alarm = 0
        self.inyectors = ""
class FilterStats:
    def __init__(self):
        self.filters = []
        self.sustain_valve = 0
        self.backwash_state = 0
        self.backwash_reason = 0
        self.next_backwash_min = 0
        self.next_backwash_hour = 0

class TerminalStats:
    def __init__(self):
        self.actuators = ActuatorStats()
        self.filters = FilterStats()
        self.irrigation_program = 0
        self.fertilization_program = 0
        self.next_irrigation_program = 0
        self.irrigation_1 = 0
        self.irrigation_2 = 0
        self.preirrigation_1 = 0
        self.preirrigation_2 = 0
        self.postirrigation_1 = 0
        self.postirrigation_2 = 0
        self.units = 0
        self.irrigation_time_1 = 0
        self.irrigation_time_2 = 0
        self.irrigation_time_3 = 0
        self.cubic_meters = 0.0
        self.irrigation_before_suspend_1 = 0
        self.irrigation_before_suspend_2 = 0
        self.flow_measured_m3h = 0.0
        self.p1 = 0.0
        self.p2 = 0.0
        self.c_prog = 0
        self.ec_asked = 0.0
        self.ph_asked = 0.0
        self.ec_average = 0.0
        self.ph_average = 0.0
        self.ec_measured = 0.0
        self.ph_measured = 0.0
        self.valves = [0] * 80
        self.inyectors = []

class ControllerState:
    def __init__(self):
        self.last_update = 0
        self.allIrrigation = dict()
        self.allFertilization = dict()
        self.allInyection = dict()
        self.username = None
        self.password = None
        self.alarm_config = AlarmConfig()
        self.alarm = Alarm()
        self.config_io = IOConfig()
        self.solape = ValveSolape()
        self.back_flushing = BackFlushing()
        self.other = OtherConfigs()

    @staticmethod
    def load_from_file(path):
        if os.path.isfile(path):
            with open(path, 'rb') as in_file:
                return (pickle.load(in_file))
        return ControllerState()

    def load_from_json(self, json):
        self.last_update = int(json['update'])
        for fert in json["fertilizer_prog"]:
            fertProg = FertilizationProgram()
            fertProg.program = fert["program"]
            fertProg.ec = fert["ec"]
            fertProg.ph = fert["ph"]
            fertProg.values_1 = fert["value_1"]
            fertProg.values_2 = fert["value_2"]
            fertProg.values_3 = fert["value_3"]
            fertProg.values_4 = fert["value_4"]
            fertProg.values_5 = fert["value_5"]
            fertProg.values_6 = fert["value_6"]
            fertProg.values_7 = fert["value_7"]
            fertProg.values_8 = fert["value_8"]
            self.allFertilization[fertProg.program] = fertProg
        for irr in json["irrigation_prog"]:
            irrProg = IrrigationProgram()
            irrProg.program = irr["program"]
            irrProg.units = irr["units"]
            irrProg.water_before_1 = irr["water_before_1"]
            irrProg.water_before_2 = irr["water_before_2"]
            irrProg.water_after_1 = irr["water_after_1"]
            irrProg.water_after_2 = irr["water_after_2"]
            irrProg.water_total_1 = irr["water_total_1"]
            irrProg.water_total_2 = irr["water_total_2"]
            irrProg.kicks = irr["kicks"]
            irrProg.fertilization_program = irr["fertilization_program"]
            irrProg.condition_program = irr["condition_program"]
            irrProg.time_start_1 = irr["time_start_1"]
            irrProg.time_start_2 = irr["time_start_2"]
            irrProg.time_between_1 = irr["time_between_1"]
            irrProg.time_between_2 = irr["time_between_2"]
            irrProg.status = irr["status"]
            irrProg.valves = irr["valves"]
            irrProg.days = irr["days"]
            self.allIrrigation[irrProg.program] = irrProg
            # TODO valves
        for iny in json["inyection_prog"]:
            inyProg = InyectionProgram()
            inyProg.program = iny["program"]
            inyProg.flow = iny["flow"]
            inyProg.function = iny["function"]
            inyProg.time_on = iny["time_on"]
            inyProg.litres_pulse = iny["litres_pulse"]
            inyProg.max_deviation = iny["max_deviation"]
            inyProg.simulator = iny["simulator"]
            self.allInyection[inyProg.program] = inyProg
        if "io_config" in json:
            json_config_io = json["io_config"]
            config_io = IOConfig()
            config_io.inyection = json_config_io["inyection"]
            config_io.filters = json_config_io["filters"]
            config_io.actuators = json_config_io["actuators"]
            config_io.valves1to16 = json_config_io["valves1to16"]
            config_io.valves17to32 = json_config_io["valves17to32"]
            config_io.valves33to48 = json_config_io["valves33to48"]
            config_io.valves49to64 = json_config_io["valves49to64"]
            config_io.valves65to80 = json_config_io["valves65to80"]
            config_io.analog_input_1 = json_config_io["analog_input_1"]
            config_io.analog_input_2 = json_config_io["analog_input_2"]
            config_io.analog_input_3 = json_config_io["analog_input_3"]
            config_io.analog_input_4 = json_config_io["analog_input_4"]
            config_io.analog_input_5 = json_config_io["analog_input_5"]
            self.config_io = config_io
        if "solape_config" in json:
            solape_json = json["solape_config"]
            solape = ValveSolape()
            solape.time = solape_json["time"]
            solape.flow = solape_json["flow"]
            solape.solape = solape_json["solape"]
            self.solape = solape
        if "other_config" in json:
            other_json = json["other_config"]
            new_other = OtherConfigs()
            new_other.booster_pump = other_json["booster_pump"]
            new_other.flow_meter_1 = other_json["flow_meter_1"]
            new_other.flow_meter_2 = other_json["flow_meter_2"]
            new_other.time_restart_program_1 = other_json["time_restart_program_1"]
            new_other.time_restart_program_2 = other_json["time_restart_program_2"]
            new_other.blower_1 = other_json["blower_1"]
            new_other.blower_2 = other_json["blower_2"]
            new_other.toff_inyector = other_json["toff_inyector"]
            new_other.manual_irrigation_units = other_json["manual_irrigation_units"]
            new_other.manual_irrigation_water_1 = other_json["manual_irrigation_water_1"]
            new_other.manual_irrigation_water_2 = other_json["manual_irrigation_water_2"]
            new_other.manual_irrigation_program = other_json["manual_irrigation_program"]
            if other_json["button_backwash_cancel"] == 1:
                new_other.button_backwash_cancel = 1
            else:
                new_other.button_backwash_cancel = 0
            if other_json["button_backwash_now"] == 1:
                new_other.button_backwash_now = 1
            else:
                new_other.button_backwash_now = 0
            self.other = new_other
        if "backflushing_config" in json:
            json_bk = json["backflushing_config"]
            backflush = BackFlushing()
            backflush.difference_backflush_kg = json_bk["difference_backflush_kg"]
            backflush.time_between_flushing_hours = json_bk["time_between_flushing_hours"]
            backflush.time_between_flushing_minutes = json_bk["time_between_flushing_minutes"]
            backflush.time_between_station_min = json_bk["time_between_station_min"]
            backflush.time_between_station_sec = json_bk["time_between_station_sec"]
            backflush.pause_between_filtering_secs = json_bk["pause_between_filtering_secs"]
            backflush.amount_of_filters = json_bk["amount_of_filters"]
            backflush.delay_differential_pressure = json_bk["delay_differential_pressure"]
            backflush.wait_after_sustain = json_bk["wait_after_sustain"]
            backflush.times_wash_before_pd_alarm = json_bk["times_wash_before_pd_alarm"]
            self.back_flushing = backflush
        if "config_alarms" in json:
            json_alarm = json["config_alarms"]
            self.alarm_config.deviation_warning_max_error_flow = json_alarm["deviation_warning_max_error_flow"]
            self.alarm_config.delay_alarms_ec_ph_secs = json_alarm["delay_alarms_ec_ph_secs"]
            self.alarm_config.delay_alarm_ph_dangerous_secs = json_alarm["delay_alarm_ph_dangerous_secs"]
            self.alarm_config.delay_alarm_ec_dangerous_secs = json_alarm["delay_alarm_ec_dangerous_secs"]
            self.alarm_config.delay_alarm_high_pressure_kg = json_alarm["delay_alarm_high_pressure_kg"]
            self.alarm_config.delay_alarm_low_pressure_secs = json_alarm["delay_alarm_low_pressure_secs"]
            self.alarm_config.delay_alarm_flow_secs = json_alarm["delay_alarm_flow_secs"]
            self.alarm_config.max_diff_warning_error_ec = json_alarm["max_diff_warning_error_ec"]
            self.alarm_config.max_diff_warning_error_ph = json_alarm["max_diff_warning_error_ph"]
            self.alarm_config.max_deviation_under_ph = json_alarm["max_deviation_under_ph"]
            self.alarm_config.max_deviation_over_ec = json_alarm["max_deviation_over_ec"]
            self.alarm_config.level_alarm_high_pressure_kg = json_alarm["level_alarm_high_pressure_kg"]
            self.alarm_config.level_alarm_low_pressure_kg = json_alarm["level_alarm_low_pressure_kg"]
            # Dejar un byte en blanco
            self.alarm_config.function_alarm_fertilizer_discontinued = json_alarm["function_alarm_fertilizer_discontinued"]
            self.alarm_config.function_alarm_ec_ph_dangerous = json_alarm["function_alarm_ec_ph_dangerous"]
            self.alarm_config.function_alarm_high_pressure = json_alarm["function_alarm_high_pressure"]
            self.alarm_config.function_alarm_dangerous_flow = json_alarm["function_alarm_dangerous_flow"]
            self.alarm_config.function_alarm_no_fertilization = json_alarm["function_alarm_no_fertilization"]
            self.alarm_config.function_alarm_no_water = json_alarm["function_alarm_no_water"]
            self.alarm_config.pulses_fertilizer_no_control = json_alarm["pulses_fertilizer_no_control"]
            self.alarm_config.pulses_needs_fertilizer = json_alarm["pulses_needs_fertilizer"]
            self.alarm_config.max_seconds_between_water_pulses = json_alarm["max_seconds_between_water_pulses"]
            self.alarm_config.over_dangerous_flow_percentage = json_alarm["over_dangerous_flow_percentage"]
            self.alarm_config.delay_secs_if_diff_ec_more_1 = json_alarm["delay_secs_if_diff_ec_more_1"]
            self.alarm_config.delay_secs_if_diff_ec_more_05 = json_alarm["delay_secs_if_diff_ec_more_05"]
            self.alarm_config.delay_secs_if_diff_ec_more_03 = json_alarm["delay_secs_if_diff_ec_more_03"]
            self.alarm_config.coefficient_correction_ec_more_1 = json_alarm["coefficient_correction_ec_more_1"]
            self.alarm_config.coefficient_correction_ec_more_05 = json_alarm["coefficient_correction_ec_more_05"]
            self.alarm_config.coefficient_correction_ec_more_03 = json_alarm["coefficient_correction_ec_more_03"]
            self.alarm_config.delay_secs_if_diff_ph_more_1 = json_alarm["delay_secs_if_diff_ph_more_1"]
            self.alarm_config.delay_secs_if_diff_ph_more_05 = json_alarm["delay_secs_if_diff_ph_more_05"]
            self.alarm_config.delay_secs_if_diff_ph_more_03 = json_alarm["delay_secs_if_diff_ph_more_03"]
            self.alarm_config.coefficient_correction_ph_more_1 = json_alarm["coefficient_correction_ph_more_1"]
            self.alarm_config.coefficient_correction_ph_more_05 = json_alarm["coefficient_correction_ph_more_05"]
            self.alarm_config.coefficient_correction_ph_more_03 = json_alarm["coefficient_correction_ph_more_03"]
            self.alarm_config.secs_first_ec_correction = json_alarm["secs_first_ec_correction"]
            self.alarm_config.secs_first_ph_correction = json_alarm["secs_first_ph_correction"]

    def save_to_file(self, filename):
        pickle.dumps(self)
        with open(filename, 'wb') as out_file:
            pickle.dump(self, out_file)

    def what_to_upload(self, other):
        toReturn = dict()
        irrigation = list()
        for x in other.allIrrigation:
            if not x in self.allIrrigation:
                irrigation.append(x)
            else:
                if self.allIrrigation[x] != other.allIrrigation[x]:
                    irrigation.append(x)
        toReturn["irrigation"] = irrigation

        fertilization = list()
        for x in other.allFertilization:
            if not x in self.allFertilization:
                fertilization.append(x)
            else:
                if self.allFertilization[x] != other.allFertilization[x]:
                    fertilization.append(x)
        toReturn["fertilization"] = fertilization

        inyection = list()
        for x in other.allInyection:
            if not x in self.allInyection:
                inyection.append(x)
            else:
                if self.allInyection[x] != other.allInyection[x]:
                    inyection.append(x)
        toReturn["inyection"] = inyection

        toReturn["backflush"] = self.back_flushing != other.back_flushing
        toReturn["alarm_config"] = self.alarm_config != other.alarm_config
        toReturn["config_io"] = self.config_io != other.config_io
        toReturn["solape"] = self.solape != other.solape
        toReturn["other"] = self.other != other.other
        return toReturn

    def __eq__(self, other):
        if self.last_update == other.last_update and \
                self.username == other.username and \
                self.password == other.password and \
                self.alarm_config == other.alarm_config and \
                self.config_io == other.config_io and \
                self.back_flushing == other.back_flushing and \
                self.solape == other.solape and \
                compare_dicts(self.allInyection, other.allInyection) and \
                compare_dicts(self.allFertilization, other.allFertilization) and \
                compare_dicts(self.allIrrigation, other.allIrrigation):
            return True
        else:
            return False
