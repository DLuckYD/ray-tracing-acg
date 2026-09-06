import os
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

import logic_scripts.config
from logic_scripts.scenes import (
    build_obj_test_scene,
    casa_scene,
    DeaverHouse_scene,
    castle_scene,
    dragon_scene,
)
from logic_scripts.parallel import render_parallel_tiles
from triangle_logic.triangle_data import build_triangle_data
from triangle_logic.triangle_bvh import build_triangle_bvh


config = logic_scripts.config


SCENES = {
    "OBJ Test Scene": build_obj_test_scene,
    "Casa": casa_scene,
    "Deaver House": DeaverHouse_scene,
    "Castle": castle_scene,
    "Dragon": dragon_scene,
}


class RayTracerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Ray / Path Tracer")
        self.root.geometry("1550x900")
        self.root.minsize(1100, 700)

        self.current_image = None
        self.preview_photo = None

        self.zoom_factor = 1.0
        self.is_rendering = False

        self._build_ui()

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=8)
        main.grid(row=0, column=0, sticky="nsew")

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=0)
        main.rowconfigure(0, weight=1)

        # ========================================================
        # LEFT SIDE
        # ========================================================

        preview_frame = ttk.LabelFrame(
            main,
            text="Render Preview",
            padding=8
        )

        preview_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)

        # --------------------------------------------------------
        # Preview toolbar
        # --------------------------------------------------------

        preview_toolbar = ttk.Frame(preview_frame)

        preview_toolbar.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 6)
        )

        ttk.Button(
            preview_toolbar,
            text="Fit",
            command=self.fit_image
        ).pack(side="left", padx=2)

        ttk.Button(
            preview_toolbar,
            text="100%",
            command=self.zoom_100
        ).pack(side="left", padx=2)

        ttk.Button(
            preview_toolbar,
            text="−",
            width=3,
            command=lambda: self._zoom_image(1 / 1.2)
        ).pack(side="left", padx=2)

        ttk.Button(
            preview_toolbar,
            text="+",
            width=3,
            command=lambda: self._zoom_image(1.2)
        ).pack(side="left", padx=2)

        self.zoom_label_var = tk.StringVar(value="100%")

        ttk.Label(
            preview_toolbar,
            textvariable=self.zoom_label_var
        ).pack(side="left", padx=(10, 0))

        # --------------------------------------------------------
        # Canvas
        # --------------------------------------------------------

        self.canvas = tk.Canvas(
            preview_frame,
            background="#202020",
            highlightthickness=0
        )

        self.canvas.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        # --------------------------------------------------------
        # Scrollbars
        # --------------------------------------------------------

        self.v_scroll = ttk.Scrollbar(
            preview_frame,
            orient="vertical",
            command=self.canvas.yview
        )

        self.v_scroll.grid(
            row=1,
            column=1,
            sticky="ns"
        )

        self.h_scroll = ttk.Scrollbar(
            preview_frame,
            orient="horizontal",
            command=self.canvas.xview
        )

        self.h_scroll.grid(
            row=2,
            column=0,
            sticky="ew"
        )

        self.canvas.configure(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set
        )

        # --------------------------------------------------------
        # Mouse controls
        # --------------------------------------------------------

        self.canvas.bind(
            "<MouseWheel>",
            self._on_mousewheel_zoom
        )

        self.canvas.bind(
            "<Button-4>",
            lambda event: self._zoom_image(1.15)
        )

        self.canvas.bind(
            "<Button-5>",
            lambda event: self._zoom_image(1 / 1.15)
        )

        self.canvas.bind(
            "<ButtonPress-1>",
            self._start_pan
        )

        self.canvas.bind(
            "<B1-Motion>",
            self._pan_image
        )

        self.canvas.bind(
            "<Double-Button-1>",
            lambda event: self.fit_image()
        )

        # ========================================================
        # RIGHT SIDE
        # ========================================================

        controls_container = ttk.Frame(main)

        controls_container.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        # Canvas so settings can scroll vertically
        controls_canvas = tk.Canvas(
            controls_container,
            width=300,
            highlightthickness=0
        )

        controls_scroll = ttk.Scrollbar(
            controls_container,
            orient="vertical",
            command=controls_canvas.yview
        )

        controls_canvas.configure(
            yscrollcommand=controls_scroll.set
        )

        controls_canvas.pack(
            side="left",
            fill="y",
            expand=False
        )

        controls_scroll.pack(
            side="right",
            fill="y"
        )

        controls = ttk.Frame(
            controls_canvas,
            padding=8
        )

        controls_window = controls_canvas.create_window(
            (0, 0),
            window=controls,
            anchor="nw"
        )

        def update_scroll_region(event=None):
            controls_canvas.configure(
                scrollregion=controls_canvas.bbox("all")
            )

        def resize_controls(event):
            controls_canvas.itemconfigure(
                controls_window,
                width=event.width
            )

        controls.bind(
            "<Configure>",
            update_scroll_region
        )

        controls_canvas.bind(
            "<Configure>",
            resize_controls
        )

        controls.columnconfigure(1, weight=1)

        row = 0

        # ========================================================
        # GENERAL SETTINGS
        # ========================================================

        ttk.Label(
            controls,
            text="Render Settings",
            font=("TkDefaultFont", 15, "bold")
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            pady=(0, 14)
        )

        row += 1

        # Scene
        ttk.Label(
            controls,
            text="Scene"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.scene_var = tk.StringVar(
            value="Castle"
        )

        self.scene_combo = ttk.Combobox(
            controls,
            textvariable=self.scene_var,
            values=list(SCENES.keys()),
            state="readonly"
        )

        self.scene_combo.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        row += 1

        # Render mode
        ttk.Label(
            controls,
            text="Renderer"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.render_mode_var = tk.StringVar(
            value="pathtrace"
        )

        self.render_combo = ttk.Combobox(
            controls,
            textvariable=self.render_mode_var,
            values=[
                "raytrace",
                "pathtrace"
            ],
            state="readonly"
        )

        self.render_combo.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        self.render_combo.bind(
            "<<ComboboxSelected>>",
            self._update_path_controls
        )

        row += 1

        # --------------------------------------------------------
        # Resolution
        # --------------------------------------------------------

        ttk.Separator(
            controls
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10
        )

        row += 1

        ttk.Label(
            controls,
            text="Resolution",
            font=("TkDefaultFont", 11, "bold")
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w"
        )

        row += 1

        ttk.Label(
            controls,
            text="Width"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.width_var = tk.IntVar(
            value=1920
        )

        ttk.Entry(
            controls,
            textvariable=self.width_var
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        row += 1

        ttk.Label(
            controls,
            text="Height"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.height_var = tk.IntVar(
            value=1080
        )

        ttk.Entry(
            controls,
            textvariable=self.height_var
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        row += 1

        # --------------------------------------------------------
        # Workers
        # --------------------------------------------------------

        ttk.Label(
            controls,
            text="Workers"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.workers_var = tk.IntVar(
            value=max(
                1,
                (os.cpu_count() or 8) - 2
            )
        )

        ttk.Entry(
            controls,
            textvariable=self.workers_var
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        row += 1

        ttk.Label(
            controls,
            text="Ray max depth"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.max_depth_var = tk.IntVar(
            value=3
        )

        ttk.Entry(
            controls,
            textvariable=self.max_depth_var
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        row += 1

        # ========================================================
        # PATH TRACING
        # ========================================================

        ttk.Separator(
            controls
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10
        )

        row += 1

        self.path_widgets = []

        path_title = ttk.Label(
            controls,
            text="Path Tracing",
            font=("TkDefaultFont", 11, "bold")
        )

        path_title.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w"
        )

        self.path_widgets.append(
            path_title
        )

        row += 1

        # SPP
        spp_label = ttk.Label(
            controls,
            text="Samples / Pixel"
        )

        spp_label.grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.path_widgets.append(
            spp_label
        )

        self.spp_var = tk.IntVar(
            value=20
        )

        spp_entry = ttk.Entry(
            controls,
            textvariable=self.spp_var
        )

        spp_entry.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        self.path_widgets.append(
            spp_entry
        )

        row += 1

        # Bounces
        bounce_label = ttk.Label(
            controls,
            text="Max Bounces"
        )

        bounce_label.grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.path_widgets.append(
            bounce_label
        )

        self.bounces_var = tk.IntVar(
            value=4
        )

        bounce_entry = ttk.Entry(
            controls,
            textvariable=self.bounces_var
        )

        bounce_entry.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        self.path_widgets.append(
            bounce_entry
        )

        row += 1

        # Russian Roulette
        self.rr_var = tk.BooleanVar(
            value=True
        )

        rr_check = ttk.Checkbutton(
            controls,
            text="Russian Roulette",
            variable=self.rr_var
        )

        rr_check.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=4
        )

        self.path_widgets.append(
            rr_check
        )

        row += 1

        rr_label = ttk.Label(
            controls,
            text="RR Start Depth"
        )

        rr_label.grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.path_widgets.append(
            rr_label
        )

        self.rr_depth_var = tk.IntVar(
            value=2
        )

        rr_entry = ttk.Entry(
            controls,
            textvariable=self.rr_depth_var
        )

        rr_entry.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        self.path_widgets.append(
            rr_entry
        )

        row += 1

        # ========================================================
        # DENOISE
        # ========================================================

        ttk.Separator(
            controls
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10
        )

        row += 1

        ttk.Label(
            controls,
            text="Denoising",
            font=("TkDefaultFont", 11, "bold")
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w"
        )

        row += 1

        self.denoise_enabled_var = tk.BooleanVar(
            value=True
        )

        ttk.Checkbutton(
            controls,
            text="Enable Denoising",
            variable=self.denoise_enabled_var
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=4
        )

        row += 1

        ttk.Label(
            controls,
            text="Mode"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.denoise_mode_var = tk.StringVar(
            value="hybrid"
        )

        ttk.Combobox(
            controls,
            textvariable=self.denoise_mode_var,
            values=[
                "hybrid",
                "bilateral",
                "adaptive",
                "median",
                "gaussian",
            ],
            state="readonly"
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        row += 1

        ttk.Label(
            controls,
            text="Passes"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.denoise_passes_var = tk.IntVar(
            value=1
        )

        ttk.Entry(
            controls,
            textvariable=self.denoise_passes_var
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        row += 1

        ttk.Label(
            controls,
            text="Threshold"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.denoise_threshold_var = tk.DoubleVar(
            value=30.0
        )

        ttk.Entry(
            controls,
            textvariable=self.denoise_threshold_var
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        row += 1

        ttk.Label(
            controls,
            text="Bilateral Strength"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        self.sigma_color_var = tk.DoubleVar(
            value=30.0
        )

        ttk.Entry(
            controls,
            textvariable=self.sigma_color_var
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4
        )

        row += 1

        # ========================================================
        # ACTIONS
        # ========================================================

        ttk.Separator(
            controls
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=12
        )

        row += 1

        self.render_button = ttk.Button(
            controls,
            text="Render",
            command=self.start_render
        )

        self.render_button.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=4
        )

        row += 1

        self.save_button = ttk.Button(
            controls,
            text="Save Image As...",
            command=self.save_image,
            state="disabled"
        )

        self.save_button.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=4
        )

        row += 1

        # Progress bar
        self.progress = ttk.Progressbar(
            controls,
            mode="indeterminate"
        )

        self.progress.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 4)
        )

        row += 1

        # Status
        self.status_var = tk.StringVar(
            value="Ready"
        )

        ttk.Label(
            controls,
            textvariable=self.status_var,
            wraplength=270
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(6, 0)
        )

        self._update_path_controls()

    # ============================================================
    # PATH TRACE ENABLE/DISABLE
    # ============================================================

    def _update_path_controls(self, event=None):
        pathtrace = (
            self.render_mode_var.get()
            == "pathtrace"
        )

        for widget in self.path_widgets:
            try:
                widget.configure(
                    state=(
                        "normal"
                        if pathtrace
                        else "disabled"
                    )
                )
            except tk.TclError:
                pass

    # ============================================================
    # RENDER START
    # ============================================================

    def start_render(self):
        if self.is_rendering:
            return

        try:
            width = int(
                self.width_var.get()
            )

            height = int(
                self.height_var.get()
            )

            workers = int(
                self.workers_var.get()
            )

            if width <= 0 or height <= 0:
                raise ValueError(
                    "Resolution must be positive."
                )

            if workers <= 0:
                raise ValueError(
                    "Workers must be at least 1."
                )

        except Exception as exc:
            messagebox.showerror(
                "Invalid Settings",
                str(exc)
            )
            return

        self.is_rendering = True

        self.render_button.configure(
            text="Rendering...",
            state="disabled"
        )

        self.save_button.configure(
            state="disabled"
        )

        self.progress.start(10)

        self.status_var.set(
            "Preparing scene..."
        )

        thread = threading.Thread(
            target=self._render_worker,
            daemon=True
        )

        thread.start()

    # ============================================================
    # RENDER THREAD
    # ============================================================

    def _render_worker(self):
        try:
            scene_display_name = (
                self.scene_var.get()
            )

            scene_builder = SCENES[
                scene_display_name
            ]

            width = int(
                self.width_var.get()
            )

            height = int(
                self.height_var.get()
            )

            workers = int(
                self.workers_var.get()
            )

            max_depth = int(
                self.max_depth_var.get()
            )

            # ----------------------------------------------------
            # Global renderer configuration
            # ----------------------------------------------------

            config.backend_mode = "cpp"

            config.render_mode = (
                self.render_mode_var.get()
            )

            config.samples_per_pixel = int(
                self.spp_var.get()
            )

            config.max_bounces = int(
                self.bounces_var.get()
            )

            config.use_russian_roulette = bool(
                self.rr_var.get()
            )

            config.rr_start_depth = int(
                self.rr_depth_var.get()
            )

            # ----------------------------------------------------
            # Denoise
            # ----------------------------------------------------

            config.enable_denoise = bool(
                self.denoise_enabled_var.get()
            )

            config.denoise_mode = (
                self.denoise_mode_var.get()
            )

            config.denoise_passes = int(
                self.denoise_passes_var.get()
            )

            config.denoise_kernel = 3

            config.denoise_threshold = float(
                self.denoise_threshold_var.get()
            )

            config.denoise_diameter = 5

            config.denoise_sigma_color = float(
                self.sigma_color_var.get()
            )

            config.denoise_sigma_space = 5.0

            # ----------------------------------------------------
            # Clear previous scene texture cache
            # ----------------------------------------------------

            config.texture_payload = None

            self.root.after(
                0,
                lambda: self.status_var.set(
                    "Building scene..."
                )
            )

            total_start = (
                time.perf_counter()
            )

            # ----------------------------------------------------
            # Build Scene
            # ----------------------------------------------------

            scene_start = (
                time.perf_counter()
            )

            (
                objects,
                background_color,
                light_position
            ) = scene_builder()

            scene_time = (
                time.perf_counter()
                - scene_start
            )

            object_count = len(objects)

            self.root.after(
                0,
                lambda: self.status_var.set(
                    f"Building triangle data...\n"
                    f"Triangles: {object_count}"
                )
            )

            # ----------------------------------------------------
            # Triangle data
            # ----------------------------------------------------

            triangle_start = (
                time.perf_counter()
            )

            config.use_triangle_backend = True

            config.triangle_data = (
                build_triangle_data(
                    objects
                )
            )

            triangle_time = (
                time.perf_counter()
                - triangle_start
            )

            # ----------------------------------------------------
            # BVH
            # ----------------------------------------------------

            self.root.after(
                0,
                lambda: self.status_var.set(
                    "Building BVH..."
                )
            )

            bvh_start = (
                time.perf_counter()
            )

            config.triangle_bvh_root = (
                build_triangle_bvh(
                    config.triangle_data
                )
            )

            bvh_time = (
                time.perf_counter()
                - bvh_start
            )

            config.use_aabb = False
            config.use_bvh = True
            config.bvh_root = None
            config.non_bvh_objects = []

            # ----------------------------------------------------
            # Render
            # ----------------------------------------------------

            self.root.after(
                0,
                lambda: self.status_var.set(
                    "Rendering..."
                )
            )

            render_start = (
                time.perf_counter()
            )

            image, stage_timings = (
                render_parallel_tiles(
                    width=width,
                    height=height,
                    objects=objects,
                    background_color=background_color,
                    light_position=light_position,
                    depth=0,
                    max_depth=max_depth,
                    num_workers=workers,
                    tile_size=128
                )
            )

            render_time = (
                time.perf_counter()
                - render_start
            )

            total_time = (
                time.perf_counter()
                - total_start
            )

            self.current_image = (
                image.copy()
            )

            self.root.after(
                0,
                self._render_finished,
                total_time,
                scene_time,
                triangle_time,
                bvh_time,
                render_time,
                object_count
            )

        except Exception as exc:
            self.root.after(
                0,
                self._render_failed,
                str(exc)
            )

    # ============================================================
    # RENDER FINISHED
    # ============================================================

    def _render_finished(
        self,
        total_time,
        scene_time,
        triangle_time,
        bvh_time,
        render_time,
        object_count
    ):
        self.is_rendering = False

        self.progress.stop()

        self.render_button.configure(
            text="Re-render",
            state="normal"
        )

        self.save_button.configure(
            state="normal"
        )

        self.status_var.set(
            f"Finished\n"
            f"Total: {total_time:.2f}s\n"
            f"Render: {render_time:.2f}s\n"
            f"BVH: {bvh_time:.2f}s\n"
            f"Triangles: {object_count}"
        )

        self.fit_image()

    # ============================================================
    # RENDER FAILED
    # ============================================================

    def _render_failed(self, error):
        self.is_rendering = False

        self.progress.stop()

        self.render_button.configure(
            text="Render",
            state="normal"
        )

        self.status_var.set(
            "Render failed"
        )

        messagebox.showerror(
            "Render Error",
            error
        )

    # ============================================================
    # IMAGE DRAW
    # ============================================================

    def _redraw_canvas_image(self):
        if self.current_image is None:
            return

        width = max(
            1,
            int(
                self.current_image.width
                * self.zoom_factor
            )
        )

        height = max(
            1,
            int(
                self.current_image.height
                * self.zoom_factor
            )
        )

        resized = self.current_image.resize(
            (width, height),
            Image.Resampling.LANCZOS
        )

        self.preview_photo = (
            ImageTk.PhotoImage(
                resized
            )
        )

        self.canvas.delete("all")

        self.canvas.create_image(
            0,
            0,
            image=self.preview_photo,
            anchor="nw"
        )

        self.canvas.configure(
            scrollregion=(
                0,
                0,
                width,
                height
            )
        )

        self.zoom_label_var.set(
            f"{self.zoom_factor * 100:.0f}%"
        )

    # ============================================================
    # FIT IMAGE
    # ============================================================

    def fit_image(self):
        if self.current_image is None:
            return

        self.root.update_idletasks()

        canvas_width = max(
            100,
            self.canvas.winfo_width()
        )

        canvas_height = max(
            100,
            self.canvas.winfo_height()
        )

        image_width = (
            self.current_image.width
        )

        image_height = (
            self.current_image.height
        )

        scale_x = (
            canvas_width
            / image_width
        )

        scale_y = (
            canvas_height
            / image_height
        )

        self.zoom_factor = min(
            scale_x,
            scale_y,
            1.0
        )

        self._redraw_canvas_image()

        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    # ============================================================
    # 100%
    # ============================================================

    def zoom_100(self):
        if self.current_image is None:
            return

        self.zoom_factor = 1.0

        self._redraw_canvas_image()

    # ============================================================
    # ZOOM
    # ============================================================

    def _zoom_image(
        self,
        multiplier
    ):
        if self.current_image is None:
            return

        new_zoom = (
            self.zoom_factor
            * multiplier
        )

        new_zoom = max(
            0.05,
            min(
                new_zoom,
                8.0
            )
        )

        self.zoom_factor = (
            new_zoom
        )

        self._redraw_canvas_image()

    # ============================================================
    # MOUSE WHEEL ZOOM
    # ============================================================

    def _on_mousewheel_zoom(
        self,
        event
    ):
        if self.current_image is None:
            return

        if event.delta > 0:
            self._zoom_image(
                1.15
            )
        else:
            self._zoom_image(
                1 / 1.15
            )

    # ============================================================
    # PAN
    # ============================================================

    def _start_pan(
        self,
        event
    ):
        self.canvas.scan_mark(
            event.x,
            event.y
        )

    def _pan_image(
        self,
        event
    ):
        self.canvas.scan_dragto(
            event.x,
            event.y,
            gain=1
        )

    # ============================================================
    # SAVE
    # ============================================================

    def save_image(self):
        if self.current_image is None:
            return

        path = filedialog.asksaveasfilename(
            title="Save Render",
            defaultextension=".png",
            filetypes=[
                (
                    "PNG image",
                    "*.png"
                ),
                (
                    "JPEG image",
                    "*.jpg *.jpeg"
                ),
                (
                    "All files",
                    "*.*"
                ),
            ]
        )

        if not path:
            return

        try:
            self.current_image.save(
                path
            )

            self.status_var.set(
                f"Saved:\n{path}"
            )

        except Exception as exc:
            messagebox.showerror(
                "Save Error",
                str(exc)
            )


# ================================================================
# APPLICATION ENTRY POINT
# ================================================================

if __name__ == "__main__":
    root = tk.Tk()

    app = RayTracerApp(
        root
    )

    root.mainloop()