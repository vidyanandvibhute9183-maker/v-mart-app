import webview

if __name__ == "__main__":
    # Creates a hardware-accelerated, true standalone Windows Application Window mapping your server
    webview.create_window("V.MART Enterprise Desktop Terminal", "http://127.0.0.1:8501", width=1200, height=800)
    webview.start()
