import os, base64, favicon, requests, json, webbrowser
import customtkinter as ctk
from tkinter import *
from PIL import *
from bs4 import *
from io import *

class BookmarkApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bookmark App")
        self.geometry("500x400")
        self.configure(fg_color='#2e2e2e')
        self.bookmarks = self.load_bookmarks()
        self.resizable(False, False)

        self.setup_ui()
        self.display_bookmarks()

        self.iconbitmap(default="./data/icons/icon.ico")

    def setup_ui(self):
        self.frame = ctk.CTkFrame(self, fg_color='#3e3e3e', corner_radius=20)
        self.frame.pack(pady=30, padx=20, fill='both', expand=False)

        self.inner_frame = ctk.CTkFrame(self.frame, fg_color='#3e3e3e', corner_radius=20)
        self.inner_frame.pack(pady=20, padx=20, fill='both', expand=False)

        self.add_button = ctk.CTkButton(self.frame, text="Add Bookmark", command=self.add_bookmark, corner_radius=10, fg_color="#ffcc00", text_color="#2e2e2e", hover_color="#ffc300")
        self.add_button.place(relx=0.22, rely=0.0000001)

        self.canvas = ctk.CTkCanvas(self.inner_frame, bg='#3e3e3e', highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self.inner_frame, orientation='vertical', command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color='#3e3e3e')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side='left', fill='both', expand=False)
        self.scrollbar.pack(side='right', fill='y')

    def load_bookmarks(self, filename='./data/bookmarks.json'):
        try:
            with open(filename, 'r') as file:
                data = file.read()
                if not data:
                    return []
                bookmarks = json.loads(data)
                for bookmark in bookmarks:
                    if bookmark['favicon']:
                        bookmark['favicon'] = base64.b64decode(bookmark['favicon'])
                return bookmarks
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_bookmarks(self, filename='./data/bookmarks.json'):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        bookmarks_to_save = []
        for bookmark in self.bookmarks:
            bookmark_copy = bookmark.copy()
            if bookmark_copy['favicon']:
                bookmark_copy['favicon'] = base64.b64encode(bookmark_copy['favicon']).decode('utf-8')
            bookmarks_to_save.append(bookmark_copy)
        with open(filename, 'w') as file:
            json.dump(bookmarks_to_save, file, indent=4)

    def fetch_website_data(self, url):
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
               title = title_tag.get_text()
            else:
               title = response.url if response.url else url
        
            icons = favicon.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
            if icons:
                favicon_response = requests.get(icons[0].url, headers={'User-Agent': 'Mozilla/5.0'})
                favicon_image = Image.open(BytesIO(favicon_response.content))
                return title, favicon_image
            return title, None
    
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {url}: {e}")
            return url, None
    
        except Exception as e:
            print(f"Error processing data for {url}: {e}")
            return url, None

    def display_bookmarks(self):
        # Clear existing bookmarks
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Display bookmarks in grid layout
        row = 0
        col = 0
        for bookmark in self.bookmarks:
            self.add_bookmark_icon(bookmark, row, col)
            col += 1
            if col > 2:  # Adjust the number of columns as needed
                col = 0
                row += 1

    def add_bookmark_icon(self, bookmark, row, col):
        frame = ctk.CTkFrame(self.scrollable_frame, fg_color='#5e5e5e', corner_radius=10, border_width=2, border_color='#ffcc00')
        frame.grid(row=row, column=col, padx=10, pady=10)
        frame.bind('<Button-3>', lambda e, bookmark=bookmark: self.show_context_menu(e, bookmark))

        icon_label = ctk.CTkLabel(frame, text="", fg_color='#5e5e5e', corner_radius=10)
        icon_label.pack(padx=5, pady=5)
        icon_label.bind('<Button-1>', lambda e, url=bookmark['url']: self.open_url(url))
        icon_label.bind('<Button-3>', lambda e, bookmark=bookmark: self.show_context_menu(e, bookmark))

        if bookmark['favicon']:
            try:
                favicon_image = Image.open(BytesIO(bookmark['favicon']))
            except UnidentifiedImageError:
                favicon_image = self.get_default_favicon()
        else:
            favicon_image = self.get_default_favicon()

        favicon_image = favicon_image.resize((48, 48), Image.LANCZOS)
        favicon_photo = ImageTk.PhotoImage(favicon_image)
        icon_label.configure(image=favicon_photo)
        icon_label.image = favicon_photo

        name_label = ctk.CTkLabel(frame, text=bookmark['title'], fg_color='#5e5e5e', text_color='#ffffff')
        name_label.pack(padx=5, pady=5)
        name_label.bind('<Button-3>', lambda e, bookmark=bookmark: self.show_context_menu(e, bookmark))

    def get_default_favicon(self):
        try:
            default_icon_path = './data/icons/default.png'
            if os.path.exists(default_icon_path):
                return Image.open(default_icon_path)
            else:
                raise FileNotFoundError("Default icon not found.")
        except Exception as e:
            print(f"Error loading default icon: {e}")
            return Image.new('RGB', (48, 48), color='#3e3e3e')

    def open_url(self, url):
        webbrowser.open(url)

    def show_context_menu(self, event, bookmark):
        context_menu = Menu(self, tearoff=0, bg='#3e3e3e', fg='#ffffff')
        context_menu.add_command(label="Edit", command=lambda: self.edit_bookmark(bookmark))
        context_menu.add_command(label="Delete", command=lambda: self.delete_bookmark(bookmark))
        context_menu.tk_popup(event.x_root, event.y_root)

    def add_bookmark(self):
        url = simpledialog.askstring("Add Bookmark", "Enter URL:", parent=self)
        if url:
            title, favicon_image = self.fetch_website_data(url)
            favicon_data = None
            if favicon_image:
                with BytesIO() as output:
                    favicon_image.save(output, format="PNG")
                    favicon_data = output.getvalue()
            self.bookmarks.append({'url': url, 'title': title, 'favicon': favicon_data})
            self.save_bookmarks()
            self.display_bookmarks()

    def edit_bookmark(self, bookmark):
        new_title = simpledialog.askstring("Edit Bookmark", "Enter new title:", initialvalue=bookmark['title'])
        new_url = simpledialog.askstring("Edit Bookmark", "Enter new URL:", initialvalue=bookmark['url'])
        if new_url:
            bookmark['title'] = new_title
            bookmark['url'] = new_url
            self.save_bookmarks()
            self.display_bookmarks()

    def delete_bookmark(self, bookmark):
        self.bookmarks.remove(bookmark)
        self.save_bookmarks()
        self.display_bookmarks()

if __name__ == "__main__":
    app = BookmarkApp()
    app.mainloop()
