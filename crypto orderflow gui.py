import tkinter as tk
from tkinter import ttk
from binance.client import Client
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import ticker

api_key = ''
api_secret = ''


def update_trades():

    # Get the current time in milliseconds
    now = int(datetime.datetime.now().timestamp() * 1000)

    global last_trade_id, volume_bar



    try : 
        if last_trade_id is None:
            # Get historical trades from the API for the symbol with a limit defined by 'qty_trades'
            trades = client.get_historical_trades(symbol=active_symbol, limit=qty_trades)
        else:
            # Fetch trades starting after last seen trade id
            trades = client.get_historical_trades(symbol=active_symbol, fromId=last_trade_id)
    except Exception as e :
        print(f"Error fetching trades: {e}")
        root.after(1000, update_trades)  # Retry after 1 second
        return

    trades = pd.DataFrame(trades)


    past_trades = trades[trades['time'] < now]
    # update last_trade_id safely
    if not past_trades.empty and pd.notna(past_trades['id'].max()):
        last_trade_id = int(past_trades['id'].max())
    else:
        last_trade_id = None



    # Filter trades that occurred in the last second
    second_trades = trades[(trades['time'] >= (now - now%1000)-interval_seconds*1000) & (trades['time'] < now - now%1000)]



    # change the type of the price column from string to float
    second_trades.loc[:, 'price'] = second_trades['price'].astype(float)
    
    # Separate aggressive sellers and buyers based on the 'isBuyerMaker' flag
    agressive_seller = second_trades[second_trades['isBuyerMaker'] == True]
    agressive_buyer = second_trades[second_trades['isBuyerMaker'] == False]
    



    # Calculate the total volume for aggressive sellers and buyers
    seller_volume_bar = agressive_seller['quoteQty'].astype(float).sum()
    buyer_volume_bar = agressive_buyer['quoteQty'].astype(float).sum()

    # Append the calculated volumes to the 'volume_bar' DataFrame
    volume_bar.loc[len(volume_bar)] = [buyer_volume_bar, seller_volume_bar]

    # If the 'volume_bar' DataFrame exceeds the defined limit 'volume_bar_number', remove the oldest entry
    if len(volume_bar) > volume_bar_number:
        # Drop the oldest row (first row)
        volume_bar = volume_bar.iloc[1:].reset_index(drop=True)




    # Select specific columns and process aggressive sellers and buyers for further analysis
    agressive_seller = agressive_seller.iloc[:, [4, 1, 2]]
    agressive_buyer = agressive_buyer.iloc[:, [4, 1, 2]]


    # take the second and milisecond part of the time
    agressive_seller['time'] = ((agressive_seller['time']%1000000)/1000)
    agressive_buyer['time'] = ((agressive_buyer['time']%1000000)/1000)

    # change the type of the qty column from string to float
    agressive_seller['qty'] = agressive_seller['qty'].astype(float)
    agressive_buyer['qty'] = agressive_buyer['qty'].astype(float)

    # Group by 'time' and 'price', summing quantities, and reset the index for further use
    agressive_seller = agressive_seller.groupby(['time', 'price']).sum().reset_index()
    agressive_buyer = agressive_buyer.groupby(['time', 'price']).sum().reset_index()





    # Update the Treeview widgets with the latest data for sellers and buyers
    update_treeview(tree_seller, agressive_seller, 'red')
    update_treeview(tree_buyer, agressive_buyer, 'green')
    
    # Update the volume bar visualization
    update_volume_bar (volume_bar)


    # Schedule the 'update_trades' function to run again just before the next second starts
    root.after(interval_seconds*1000 - (int(datetime.datetime.now().timestamp() * 1000) % 1000) , update_trades)

def update_volume_bar (volume_bar) : 

    # Get the current y-axis limits (by limit it's the last unit number in the y axis)
    ymin, ymax = ax.get_ylim()

    # Clear the current axes (meaning clearning the bar chart)
    ax.clear()


    # Fixed bar width
    bar_width = 0.95

    # Plotting taker buy volume in green
    ax.bar(range(1, len(volume_bar)+1), volume_bar['buyer_volume_bar'], color='green',width=bar_width, label='Taker Buy Volume')
    # Plotting taker sell volume in red
    ax.bar(range(1, len(volume_bar)+1), -volume_bar['seller_volume_bar'], color='red',width=bar_width, label='Taker Sell Volume')

    # format y-axis labels as absolute values
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{abs(int(x)):,}'))

    # Ensure the y-axis is symmetrical around zero by finding the maximum volume in both seller take and buyer taker
    max_volume = max(volume_bar['buyer_volume_bar'].max(), volume_bar['seller_volume_bar'].max())

    # Set margins to zero for x and y axes to make the plot flush against the borders (to make it fill the plot)
    ax.margins(x=0, y=0)

    # Set y-axis limits symmetrically around zero, with a 10% padding above the max volume
    ax.set_ylim(min(-max_volume-(max_volume/10),ymin), max(max_volume+(max_volume/10),ymax))

    # Adjust x-axis limits so when there are few bars they won't take the whole plot.
    ax.set_xlim(len(volume_bar) + 0.5 - volume_bar_number, len(volume_bar) + 0.5)

    # Remove x-axis labels for a cleaner look
    ax.set_xticks([])
    ax.set_xticklabels([])

    # Move y-axis ticks and labels to the right side of the plot
    ax.yaxis.tick_right()

    # Adjust the layout to make sure the plot fills the canvas properly
    plt.tight_layout()

    # Draw the updated plot on the canvas
    canvas.draw()

def update_treeview(treeview, data, color):

    # Clear existing data from the treeview
    for row in treeview.get_children():
        treeview.delete(row)

    # Initialize variables to keep track of the last time value and the current row color tag
    last_time = None
    current_tag = 'white'  # Start with the white tag

    # Insert new data with alternating row colors based on time
    for index, row in data.iterrows():

        # Change the row color tag when the time value changes
        if last_time is None or row['time'] != last_time:
            current_tag = color if current_tag == 'white' else 'white'
        # Insert the row into the treeview with the current color tag
        treeview.insert("", "end", values=list(row), tags=(current_tag,))
        # Update the last_time variable to the current row's time value
        last_time = row['time']

    # Configure the treeview tags to set the background colors
    treeview.tag_configure('white', background='white')
    treeview.tag_configure('red', background='#ff4d4d')
    treeview.tag_configure('green', background='#85e085')

def on_press(event):

    # Event handler for mouse press event
    # Stores the event information globally to be accessed later
    global press_event
    press_event = event

def on_release(event):

    # Event handler for mouse release event
    # Resets the global press_event variable to None
    global press_event
    press_event = None

def on_motion(event):

    # Event handler for mouse motion event (while a mouse button is pressed)   
    global press_event
    # Check if there is a previous press event and current event has valid xdata
    if press_event is None or event is None or event.xdata is None or press_event.xdata is None:
        return
    
    # Calculate the difference in x and y coordinates between the current event and the previous press event
    dx = event.xdata - press_event.xdata
    dy = event.ydata - press_event.ydata

    # Get the current y-axis limits
    ymin, ymax = ax.get_ylim()

    if press_event.ydata > 0:
        # If the press event occurred above the 0 line, adjust the y-axis limits accordingly
        ax.set_ylim(min (ymin, -ymax) + dy/2, max (-ymin, ymax) - dy/2)
    else:
        # If the press event occurred below the 0 line, adjust the y-axis limits accordingly
        ax.set_ylim(min (ymin, -ymax) - dy/2, max (-ymin, ymax) + dy/2)

    # Redraw the canvas to reflect the new y-axis limits 
    canvas.draw()

def on_enter(event):
    # Change cursor to hand with pointing finger when entering the plot area
    event.widget.config(cursor="sb_v_double_arrow")

def on_leave(event):
    # Change cursor back to default when leaving the plot area
    event.widget.config(cursor="")

# Button to apply ticker change
def set_symbol():
    global last_trade_id, volume_bar, active_symbol

    new_symbol = symbol_var.get().strip().upper()
    if not new_symbol:
        print("Empty symbol ignored")
        return

    try:
        # Validate symbol by pinging Binance
        client.get_symbol_info(new_symbol)
    except Exception as e:
        print(f"Invalid symbol: {new_symbol}")
        return

    # If we reach here, symbol is valid
    active_symbol = new_symbol
    last_trade_id = None
    volume_bar = pd.DataFrame(columns=['buyer_volume_bar', 'seller_volume_bar'])

    ax.clear()
    canvas.draw()

    for tree in (tree_seller, tree_buyer):
        for row in tree.get_children():
            tree.delete(row)

def set_interval():
    global interval_seconds, volume_bar, last_trade_id

    try:
        new_val = int(interval_var.get())
        if new_val <= 0:
            raise ValueError("Must be positive")
    except Exception:
        print("Invalid interval value")
        return

    interval_seconds = new_val
    last_trade_id = None
    volume_bar = pd.DataFrame(columns=['buyer_volume_bar', 'seller_volume_bar'])

    # Clear chart
    ax.clear()
    canvas.draw()

    # Clear treeviews
    for tree in (tree_seller, tree_buyer):
        for row in tree.get_children():
            tree.delete(row)



try:
    client = Client(api_key, api_secret)
    client.get_system_status()  # Test API connection
except Exception as e:
    print(f"Error initializing Binance client: {e}")
    root.quit()
    exit(1)


# the amount of trades to be retreived from Binance client at the first time (from the last trade)
qty_trades = 100

last_trade_id = None

interval_seconds = 1  # default aggregation window in seconds


# Initialize the Tkinter app
root = tk.Tk()
root.title("Aggressive Traders")

# Set fixed window size
window_width = 600
window_height = 1000
root.geometry(f"{window_width}x{window_height}")


# --- Row 0: Controls inside a frame ---
control_frame = tk.Frame(root)
control_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

quit_button = tk.Button(control_frame, text="Quit", command=root.quit)
quit_button.pack(side="left", fill="x", expand=True)

symbol_var = tk.StringVar(value="BTCUSDT")
active_symbol = "BTCUSDT"

symbol_entry = tk.Entry(control_frame, textvariable=symbol_var)
symbol_entry.pack(side="left", fill="x", expand=True)

apply_button = tk.Button(control_frame, text="Enter", command=set_symbol)
apply_button.pack(side="left", fill="x", expand=True)

interval_var = tk.StringVar(value="1")
interval_entry = tk.Entry(control_frame, textvariable=interval_var)
interval_entry.pack(side="left", fill="x", expand=True)

interval_button = tk.Button(control_frame, text="Set Interval", command=set_interval)
interval_button.pack(side="left", fill="x", expand=True)

# --- Row 1: Treeviews ---
tree_seller = ttk.Treeview(root, columns=('time', 'price', 'qty'), show='headings')
tree_seller.grid(row=1, column=0, sticky="nsew")

tree_buyer = ttk.Treeview(root, columns=('time', 'price', 'qty'), show='headings')
tree_buyer.grid(row=1, column=1, sticky="nsew")

# --- Configure seller treeview headers ---
tree_seller.heading('time', text='Time (s)')
tree_seller.heading('price', text='Price')
tree_seller.heading('qty', text='Quantity')

tree_seller.column('time', anchor='center', width=100)
tree_seller.column('price', anchor='center', width=100)
tree_seller.column('qty', anchor='center', width=100)

# --- Configure buyer treeview headers ---
tree_buyer.heading('time', text='Time (s)')
tree_buyer.heading('price', text='Price')
tree_buyer.heading('qty', text='Quantity')

tree_buyer.column('time', anchor='center', width=100)
tree_buyer.column('price', anchor='center', width=100)
tree_buyer.column('qty', anchor='center', width=100)

# --- Row 2: Chart ---
fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=2, column=0, columnspan=2, sticky="ew")
canvas.get_tk_widget().configure(height=350)  # adjust this value

# --- Grid weights ---
root.grid_rowconfigure(1, weight=10)
root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)





# Initialize volume bar data with an empty DataFrame
volume_bar_number = 30
volume_bar = pd.DataFrame(columns=['buyer_volume_bar', 'seller_volume_bar'])





# Schedule the first call to update_trades
root.after(1000 - (int(datetime.datetime.now().timestamp() * 1000) % 1000) , update_trades)



# Initialize press_event variable to None for tracking mouse events
press_event = None

# Connect mouse events to the corresponding handler functions
canvas.mpl_connect("button_press_event", on_press)
canvas.mpl_connect("button_release_event", on_release)
canvas.mpl_connect("motion_notify_event", on_motion)

canvas.get_tk_widget().bind("<Enter>", on_enter)
canvas.get_tk_widget().bind("<Leave>", on_leave)



# Start the Tkinter event loop
root.mainloop()