import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
from advanced_desensitize_markdown import (
    desensitize_text_file,
    restore_text_file,
    process_directory,
    process_directory_restore
)


class DesensitizeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown数字脱敏工具")
        self.root.geometry("800x600")
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 模式选择
        mode_frame = ttk.LabelFrame(main_frame, text="操作模式", padding="10")
        mode_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="desensitize")
        ttk.Radiobutton(mode_frame, text="脱敏模式", variable=self.mode_var, value="desensitize", 
                       command=self.on_mode_change).grid(row=0, column=0, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="还原模式", variable=self.mode_var, value="restore",
                       command=self.on_mode_change).grid(row=0, column=1, padx=(0, 20))
        
        # 文件/目录选择
        input_frame = ttk.LabelFrame(main_frame, text="输入设置", padding="10")
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Label(input_frame, text="输入:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.input_path = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_path, width=50).grid(row=0, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(input_frame, text="浏览", command=self.browse_input).grid(row=0, column=2)
        
        # 映射文件（仅还原模式显示）
        self.mapping_frame = ttk.LabelFrame(main_frame, text="映射文件（还原模式）", padding="10")
        self.mapping_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.mapping_frame.grid_remove()  # 初始隐藏
        
        ttk.Label(self.mapping_frame, text="映射文件:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.mapping_path = tk.StringVar()
        ttk.Entry(self.mapping_frame, textvariable=self.mapping_path, width=50).grid(row=0, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(self.mapping_frame, text="浏览", command=self.browse_mapping).grid(row=0, column=2)
        
        # 输出设置
        output_frame = ttk.LabelFrame(main_frame, text="输出设置", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Label(output_frame, text="输出:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.output_path = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_path, width=50).grid(row=0, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(output_frame, text="浏览", command=self.browse_output).grid(row=0, column=2)
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.process_btn = ttk.Button(button_frame, text="开始处理", command=self.process_files)
        self.process_btn.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(button_frame, text="清空", command=self.clear_fields).grid(row=0, column=1)
        
        # 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="10")
        log_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        main_frame.rowconfigure(5, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        # 初始模式设置
        self.on_mode_change()
        
    def on_mode_change(self):
        """模式改变时的处理"""
        if self.mode_var.get() == "restore":
            self.mapping_frame.grid()
        else:
            self.mapping_frame.grid_remove()
    
    def browse_input(self):
        """浏览输入文件或目录"""
        mode = self.mode_var.get()
        
        if mode == "desensitize":
            # 脱敏模式：可以是文件或目录
            path = filedialog.askdirectory(title="选择输入目录") if messagebox.askyesno("选择类型", "选择目录吗？\n选择\"是\"选择目录，选择\"否\"选择文件") else filedialog.askopenfilename(
                title="选择输入文件", 
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("Markdown文件", "*.md"), 
                    ("CSV文件", "*.csv"),
                    ("JSON文件", "*.json"),
                    ("XML文件", "*.xml"),
                    ("HTML文件", "*.html"),
                    ("Python文件", "*.py"),
                    ("JavaScript文件", "*.js"),
                    ("TypeScript文件", "*.ts"),
                    ("其他文本文件", "*.*")
                ]
            )
        else:
            # 还原模式：可以是文件或目录
            path = filedialog.askdirectory(title="选择输入目录") if messagebox.askyesno("选择类型", "选择目录吗？\n选择\"是\"选择目录，选择\"否\"选择文件") else filedialog.askopenfilename(
                title="选择输入文件", 
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("Markdown文件", "*.md"), 
                    ("CSV文件", "*.csv"),
                    ("JSON文件", "*.json"),
                    ("XML文件", "*.xml"),
                    ("HTML文件", "*.html"),
                    ("Python文件", "*.py"),
                    ("JavaScript文件", "*.js"),
                    ("TypeScript文件", "*.ts"),
                    ("其他文本文件", "*.*")
                ]
            )
        
        if path:
            self.input_path.set(path)
            
            # 自动设置输出路径
            if os.path.isfile(path):
                base_name = os.path.splitext(path)[0]
                ext = os.path.splitext(path)[1]
                if mode == "desensitize":
                    output_path = f"{base_name}_desensitized{ext}"
                else:  # restore
                    output_path = f"{base_name}_restored{ext}"
            else:  # 目录
                if mode == "desensitize":
                    output_path = f"{path}_desensitized"
                else:  # restore
                    output_path = f"{path}_restored"
            
            self.output_path.set(output_path)
    
    def browse_mapping(self):
        """浏览映射文件"""
        path = filedialog.askopenfilename(
            title="选择映射文件", 
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if path:
            self.mapping_path.set(path)
    
    def browse_output(self):
        """浏览输出文件或目录"""
        mode = self.mode_var.get()
        
        if mode == "desensitize":
            # 脱敏模式：可以是文件或目录
            path = filedialog.askdirectory(title="选择输出目录") if messagebox.askyesno("选择类型", "选择目录吗？\n选择\"是\"选择目录，选择\"否\"选择文件") else filedialog.asksaveasfilename(
                title="选择输出文件", 
                defaultextension=".txt",
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("Markdown文件", "*.md"), 
                    ("CSV文件", "*.csv"),
                    ("JSON文件", "*.json"),
                    ("XML文件", "*.xml"),
                    ("HTML文件", "*.html"),
                    ("Python文件", "*.py"),
                    ("JavaScript文件", "*.js"),
                    ("TypeScript文件", "*.ts"),
                    ("所有文件", "*.*")
                ]
            )
        else:
            # 还原模式：可以是文件或目录
            path = filedialog.askdirectory(title="选择输出目录") if messagebox.askyesno("选择类型", "选择目录吗？\n选择\"是\"选择目录，选择\"否\"选择文件") else filedialog.asksaveasfilename(
                title="选择输出文件", 
                defaultextension=".txt",
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("Markdown文件", "*.md"), 
                    ("CSV文件", "*.csv"),
                    ("JSON文件", "*.json"),
                    ("XML文件", "*.xml"),
                    ("HTML文件", "*.html"),
                    ("Python文件", "*.py"),
                    ("JavaScript文件", "*.js"),
                    ("TypeScript文件", "*.ts"),
                    ("所有文件", "*.*")
                ]
            )
        
        if path:
            self.output_path.set(path)
    
    def log_message(self, message):
        """在日志中添加消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_fields(self):
        """清空所有字段"""
        self.input_path.set("")
        self.output_path.set("")
        self.mapping_path.set("")
        self.log_text.delete(1.0, tk.END)
        self.status_var.set("已清空")
    
    def process_files(self):
        """处理文件"""
        try:
            input_path = self.input_path.get()
            output_path = self.output_path.get()
            mode = self.mode_var.get()
            
            if not input_path:
                messagebox.showerror("错误", "请输入输入路径")
                return
            
            if not output_path:
                messagebox.showerror("错误", "请输入输出路径")
                return
            
            if mode == "restore" and not self.mapping_path.get():
                messagebox.showerror("错误", "还原模式需要指定映射文件")
                return
            
            self.status_var.set("处理中...")
            self.process_btn.config(state="disabled")
            
            # 清空日志
            self.log_text.delete(1.0, tk.END)
            
            if os.path.isfile(input_path):
                # 处理单个文件
                if mode == "desensitize":
                    self.log_message(f"开始脱敏文件: {input_path}")
                    desensitize_text_file(input_path, output_path)
                    self.log_message(f"脱敏完成: {output_path}")
                else:  # restore
                    mapping_file = self.mapping_path.get()
                    self.log_message(f"开始还原文档: {input_path}")
                    restore_text_file(input_path, mapping_file, output_path)
                    self.log_message(f"还原完成: {output_path}")
            else:
                # 处理目录
                if mode == "desensitize":
                    self.log_message(f"开始脱敏目录: {input_path}")
                    process_directory(input_path, output_path)
                    self.log_message(f"目录脱敏完成: {output_path}")
                else:  # restore
                    mapping_file = self.mapping_path.get()
                    self.log_message(f"开始还原目录: {input_path}")
                    process_directory_restore(input_path, mapping_file, output_path)
                    self.log_message(f"目录还原完成: {output_path}")
            
            self.log_message("处理完成！")
            self.status_var.set("处理完成")
            messagebox.showinfo("完成", "处理完成！")
            
        except Exception as e:
            error_msg = f"处理出错: {str(e)}"
            self.log_message(error_msg)
            self.status_var.set("处理出错")
            messagebox.showerror("错误", error_msg)
        
        finally:
            self.process_btn.config(state="normal")


def main():
    root = tk.Tk()
    app = DesensitizeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()