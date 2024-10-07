def process_data(data):
    processed = []
    for i in range(len(data)):
        processed.append(data[i] * 2)
    return processed

def filter_data(data, threshold):
    filtered = []
    for item in data:
        if item > threshold:
            filtered.append(item)
    return filtered