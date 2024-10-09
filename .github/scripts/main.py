from data_processor import process_data
from utils import calculate_average, format_output

def main():
    data = [1, 2, 3, 4, 5]
    processed_data = process_data(data)
    average = calculate_average(processed_data)
    formatted_output = format_output(average)
    print(formatted_output)

if __name__ == "__main__":
    main()