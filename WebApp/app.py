import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import time
import json
import os
from datetime import datetime, timedelta

# Kết nối đến cơ sở dữ liệu SQLite
conn = sqlite3.connect("tasks.db")
c = conn.cursor()

# Tạo bảng nếu chưa tồn tại
c.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    due_date DATE,
    completed BOOLEAN
)
''')
conn.commit()

# Hàm thêm nhiệm vụ
def add_task(name, description, due_date):
    c.execute("INSERT INTO tasks (name, description, due_date, completed) VALUES (?, ?, ?, ?)", (name, description, due_date, False))
    conn.commit()

# Hàm cập nhật nhiệm vụ
def update_task(task_id, name, description, due_date):
    c.execute("UPDATE tasks SET name = ?, description = ?, due_date = ? WHERE id = ?", (name, description, due_date, task_id))
    conn.commit()

# Hàm xóa nhiệm vụ
def delete_task(task_id):
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()

# Hàm cập nhật trạng thái hoàn thành của nhiệm vụ
def update_task_status(task_id, completed):
    c.execute("UPDATE tasks SET completed = ? WHERE id = ?", (completed, task_id))
    conn.commit()

# Hàm lấy tất cả nhiệm vụ dưới dạng DataFrame
def get_tasks_df():
    c.execute("SELECT * FROM tasks")
    rows = c.fetchall()
    tasks_df = pd.DataFrame(rows, columns=["ID", "Tên nhiệm vụ", "Mô tả", "Ngày hoàn thành", "Hoàn thành"])
    return tasks_df

# Hàm nhắc nhở nhiệm vụ chưa hoàn thành trước 1 ngày
def get_due_soon_tasks():
    today = datetime.now().date()
    reminder_date = today + timedelta(days=1)
    c.execute("SELECT * FROM tasks WHERE completed = 0 AND due_date = ?", (reminder_date,))
    return c.fetchall()

# Hàm thông báo nhiệm vụ đã hết hạn
def get_expired_tasks():
    today = datetime.now().date()
    expire_date = today - timedelta(days=1)
    c.execute("SELECT * FROM tasks WHERE completed = 0 AND due_date = ?", (expire_date,))
    return c.fetchall()

# Hàm ghi nhận và chấm dứt chuỗi ngày duy trì
def day_streak(filename="streak.json"):

    # Lấy ngày hiện tại
    today = datetime.now().date()
    
    # Nếu file không tồn tại, tạo file mới với dữ liệu ban đầu
    if not os.path.exists(filename):
        data = {
            "last_date": today.strftime("%Y-%m-%d"),
            "streak": 1
        }
        with open(filename, "w") as file:
            json.dump(data, file)
        print("Đã tạo file mới và bắt đầu chuỗi ngày duy trì từ ngày thứ 1.")
        return 1
    
    # Nếu file tồn tại, đọc dữ liệu từ file
    with open(filename, "r") as file:
        data = json.load(file)
        last_date = datetime.strptime(data["last_date"], "%Y-%m-%d").date()
        streak = data["streak"]

    # Kiểm tra chuỗi ngày
    if last_date == today - timedelta(days=1):  # Ngày hôm qua
        streak += 1
    elif last_date != today - timedelta(days=1):  # Nếu là ngày đầu tiên hoặc không liên tục
        if last_date != today:
            streak = 1

    # Cập nhật dữ liệu và ghi vào file
    data = {
        "last_date": today.strftime("%Y-%m-%d"),
        "streak": streak
    }
    with open(filename, "w") as file:
        json.dump(data, file)

    return streak

# Hiển thị chuỗi ngày duy trì lên sidebar
streak = day_streak() 
st.sidebar.write(f"Chuỗi ngày bạn truy cập: {streak}")

# Hiển thị ngày tháng năm
date = datetime.now().date()
st.sidebar.write(f"Ngày hiện tại: {date}")

# Tiêu đề
st.title("Ứng dụng quản lý thời gian và công việc")
print("Bản demo: Nó còn quá sơ khai để có thể sử dụng :((")
st.markdown("---")

# Phần thêm nhiệm vụ mới
add_task_gui = st.sidebar.popover("Thêm nhiệm vụ")
with add_task_gui:
    task_name = st.text_input("Tên nhiệm vụ",max_chars=50)
    task_description = st.text_area("Mô tả nhiệm vụ",max_chars=200)
    task_due_date = st.date_input("Ngày hoàn thành")

    if st.button("Tạo nhiệm vụ"):
        if task_name and task_due_date:
            add_task(task_name, task_description, task_due_date)
            st.toast("Đã thêm nhiệm vụ thành công!")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Vui lòng nhập đầy đủ thông tin")

# Hiển thị danh sách nhiệm vụ dưới dạng bảng
all_tasks_list, deadline_tasks_list = st.columns([3,1])

with all_tasks_list:
    st.header("Danh sách nhiệm vụ")
    tasks_df = get_tasks_df()
    if not tasks_df.empty:
        for index, row in tasks_df.iterrows():
            task_id = row['ID']
            task_name = row['Tên nhiệm vụ']
            task_description = row['Mô tả']
            task_due_date = row['Ngày hoàn thành']
            task_completed = row['Hoàn thành']
            
            # Hiển thị thông tin nhiệm vụ
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 2, 1], vertical_alignment="bottom")
                with col1:
                    st.write(f"ID: {task_id} -  **{task_name}**")
                    st.write(f"Hạn: {task_due_date}")
                    st.caption(f"{task_description}")
                    
                # Chỉnh sửa nhiệm vụ
                with col2:
                        with st.popover("Chỉnh sửa"):
                            new_name = st.text_input("Tên nhiệm vụ", value=task_name, key=f"new_name_{task_id}")
                            new_description = st.text_area("Mô tả nhiệm vụ", value=task_description, key=f"new_desc_{task_id}")
                            new_due_date = st.date_input("Ngày hoàn thành", value=datetime.strptime(task_due_date, "%Y-%m-%d").date(), key=f"new_date_{task_id}")
                            if st.button("Lưu thay đổi", key=f"save_{task_id}"):
                                update_task(task_id, new_name, new_description, new_due_date)
                                st.toast("Đã cập nhật nhiệm vụ!")
                                time.sleep(1)
                                st.rerun()
                                
                # Xóa nhiệm vụ
                with col3:
                    if st.button("Xóa", key=f"delete_{task_id}"):
                        delete_task(task_id)
                        st.toast("Đã xóa nhiệm vụ!")
                        time.sleep(1)
                        st.rerun()
                        
                        
                # Hoàn thành nhiệm vụ
                completed = st.checkbox("Hoàn thành", value=task_completed, key=f"complete_{task_id}")
                if completed != task_completed:
                    update_task_status(task_id, completed)
                    st.toast("Cập nhật trạng thái hoàn thành!")
                    time.sleep(1)
                    st.rerun()
    else:
        st.info("Hiện chưa có nhiệm vụ nào.")

# Hiển thị danh sách nhiệm vụ cần hoàn thành
with deadline_tasks_list:
    st.header("Nhiệm vụ cần hoàn thành sớm")
    due_soon_tasks = get_due_soon_tasks()
    if due_soon_tasks:
        for task in due_soon_tasks:
            st.warning(f"Nhiệm vụ '{task[1]}' cần hoàn thành vào ngày {task[3]}")
    else:
        st.info("Không có nhiệm vụ nào cần hoàn thành sớm")

# Hiển thị danh sách nhiệm vụ đã hết hạn
st.header("Nhiệm vụ đã hết hạn")
expired_tasks = get_expired_tasks()
if expired_tasks:
    for task in expired_tasks:
        st.error(f"Nhiệm vụ '{task[1]}' đã hết hạn vào ngày {task[3]}")
else:
    st.info("không có nhiệm vụ nào đã hết hạn")

# Đóng kết nối sau khi dùng xong
conn.close()
