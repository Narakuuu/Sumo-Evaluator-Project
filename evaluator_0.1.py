import os
import importlib.util
import traci
import csv
from sumolib import checkBinary
import xml.etree.ElementTree as ET
from multiprocessing import Pool, freeze_support

# 导入用户定义的动态管控函数
spec = importlib.util.spec_from_file_location("dynamic_control", "D:/sumo_test/pytest/penetration20/dynamic_control.py")
dynamic_control_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dynamic_control_module)

# 输出CSV文件路径
output_csv = 'D:\sumo_test\pytest\output.csv'

# 指定包含SUMO配置文件的根文件夹
root_folder = "D:\sumo_test\pytest"

# 定义要收集的指标字段列表
fields = ['Experiments', 'AverageDuration', 'VehicleCount']

# 创建CSV文件并写入字段名称
with open(output_csv, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(fields)

# 处理tripinfo.xml文件,计算相关指标数据
def parse_tripinfo_file(tripinfo_file):
    try:
        tree = ET.parse(tripinfo_file)
        root = tree.getroot()

        durations = []
        vehicle_count = len(root.findall('tripinfo'))

        for tripinfo in root.iter('tripinfo'):
            duration = float(tripinfo.attrib['duration'])
            durations.append(duration)

        return durations, vehicle_count
    except ET.ParseError as e:
        print(f"Error parsing {tripinfo_file}: {e}")
        return None, None

def calculate_average_duration(durations):
    if len(durations) > 0:
        average_duration = sum(durations) / len(durations)
    else:
        average_duration = 0.0

    return average_duration

# 执行SUMO仿真，调用用户定义的动态管控函数
def run_simulation(sumocfg_path):
    # 提取sumocfg文件的名称
    sumocfg_filename = os.path.basename(sumocfg_path)
    info_file="tripinfo_"+ sumocfg_filename[:-8] +".xml"

    # 根据sumocfg_path加载SUMO配置文件并执行仿真
    # 在适当的时机调用 dynamic_control_module.run()

    # Load the SUMO configuration file and tripinfo-output
    sumoBinary = checkBinary('sumo')
    traci.start([sumoBinary, "-c", sumocfg_path,"--tripinfo-output",os.path.join(root_folder, info_file)])

    # Call the user-defined dynamic control function
    dynamic_control_module.run()
 
    # Run the simulation
   #while traci.simulation.getMinExpectedNumber() > 0:
        #traci.simulationStep()

    # Close the simulation
    traci.close()
  
  # 解析tripinfo.xml文件并提取指标数据
    durations, vehicle_count = parse_tripinfo_file(os.path.join(root_folder, info_file))
    print("file and vehicle:", info_file, vehicle_count)
    average_duration = calculate_average_duration(durations)
    print("file and vehicle:", info_file, average_duration)

    # 返回实验名称、平均持续时间和车辆总数
    return sumocfg_filename[:-8], average_duration, vehicle_count    

def simulate_with_dynamic_control(sumocfg_path):
    # 执行仿真
    return run_simulation(sumocfg_path)
    
if __name__ == "__main__":

    # 获取包含SUMO配置文件的文件路径列表
    sumocfg_files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            # 找到以.sumocfg结尾的文件
            if filename.endswith(".sumocfg"):
                sumocfg_path = os.path.join(dirpath, filename)
                sumocfg_files.append(sumocfg_path)
    #print("sumocfg_files:" , sumocfg_files)

    batch_size = 5  # 每个批次的任务数量
    num_batches = len(sumocfg_files) // batch_size
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = (i + 1) * batch_size
        batch_files = sumocfg_files[start_idx:end_idx]
    
    # 创建进程池并行处理多个仿真任务
        with Pool() as pool:
            results = pool.map(simulate_with_dynamic_control, sumocfg_files)
        

    # 将结果写入CSV文件
        with open(output_csv, mode='a', newline='') as file:
            writer = csv.writer(file) 
            filtered_results = [result for result in results if result is not None]
            #print("filtered_results=", filtered_results)
            writer.writerows(filtered_results)
    
    # 处理剩余的任务
    remaining_files = sumocfg_files[num_batches * batch_size:]
    if remaining_files:
        with Pool() as pool:
            results = pool.map(simulate_with_dynamic_control, remaining_files)

        # 将结果写入CSV文件
        with open(output_csv, mode='a', newline='') as file:
            writer = csv.writer(file)
            filtered_results = [result for result in results if result is not None]
            writer.writerows(filtered_results)