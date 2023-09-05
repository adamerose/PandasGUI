def main():
    try:
        import sys
        from pandasgui import show
        import os
        import pandas as pd

        # Get paths of drag & dropped files and prepare to open them in the GUI
        file_paths = sys.argv[1:]
        print("Opening files with PandasGUI: \n" + '\n'.join(file_paths))
        if file_paths:
            file_dataframes = {}
            for path in file_paths:
                if os.path.isfile(path) and (path.endswith('.csv') or path.endswith('.pkl')):
                    if path.endswith('.csv') :
                        df = pd.read_csv(path)
                    if path.endswith('.pkl'):
                        df = pd.read_pickle(path)
                    filename = os.path.split(path)[1]
                    file_dataframes[filename] = df
            show(**file_dataframes)
    except Exception as e:
        import traceback
        traceback.print_exc()
        input()

if __name__ == '__main__':
    main()