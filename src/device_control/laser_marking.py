
# On Windows, create a shared folder by right-clicking the folder -> Properties -> Sharing tab -> Click Share.
# Ensure network discovery and file sharing are enabled.
# Get the shared path (e.g., \\DESKTOP-5TA44U5\python_web).
import os


class LaserMarking:
    def __init__(self, shared_folder_path):
        """
        Initialize LaserMarking class and set shared folder path.
        :param shared_folder_path: Shared folder path。
        """
        self.shared_folder_path = shared_folder_path

        # Check if shared folder path exists
        if not os.path.exists(self.shared_folder_path):
            raise ValueError(f"Specified shared folder path does not exist: {self.shared_folder_path}")

    def write_data_to_file(self, data):
        """
        Write data to txt file in shared folder.
        :param data: Data (number) to write to file
        """
        file_path = os.path.join(self.shared_folder_path, "received_data.txt")

        # Open file and write data
        try:
            with open(file_path, "a") as file:
                file.write(str(data) + "\n")
            print(f"Data {data} has been successfully written to {file_path}")
        except Exception as e:
            print(f"Error occurred while writing to file: {e}")


# Example usage:
if __name__ == "__main__":
    shared_folder_path = r"\\192.168.1.3\python_web"
    laser_marking = LaserMarking(shared_folder_path)

    laser_marking.write_data_to_file(12345)
