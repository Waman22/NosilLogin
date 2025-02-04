import qrcode

# URL for the Flask route
data = "http://localhost:5001/signin"  # Replace with your actual Flask URL

# Creating an instance of QRCode class
qr = qrcode.QRCode(version = 1,
                   box_size = 10,
                   border = 5)

# Adding data to the instance 'qr'
qr.add_data(data)

# Ensure QR code fits the data
qr.make(fit = True)

# Create image of QR code with red color on white background
img = qr.make_image(fill_color = 'red', back_color = 'white')

# Save the QR code image
img.save('signin_qr_code.png')

# Optionally, show the QR code image
img.show()
