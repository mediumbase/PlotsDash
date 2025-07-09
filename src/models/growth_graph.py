import io
import base64
import matplotlib.pyplot as plt

def generate_growth_graph():
    """Generate a growth graph using Matplotlib."""
    # Example growth data
    growth_data = {
        "Plant A": [10, 15, 20, 25, 30],
        "Plant B": [5, 10, 15, 20, 25],
        "Plant C": [8, 12, 16, 20, 24]
    }

    # Create the plot
    plt.figure(figsize=(6, 4))
    for plant, rates in growth_data.items():
        plt.plot(rates, label=plant)
    plt.title('Plant Growth Over Time')
    plt.xlabel('Time (Days)')
    plt.ylabel('Height (cm)')
    plt.legend()
    plt.grid(True)

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Encode the image to base64
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64