/* =================================================================
   Fluorímetro de Bajo Costo - Microtubo 0.5 mL + Adafruit AS7341
   - Eje X: Canal para LED de 3 mm
   - Eje Y (90°): Cavidad y montaje para sensor espectral AS7341
   ================================================================= */

$fn = 60;

// --- Microtubo de 0.5 mL ---
tube_body_dia    = 8.4;
cone_tip_dia     = 4.5;
cone_height      = 12.0;
cylinder_height  = 16.0;
rim_dia          = 13.5;
rim_depth        = 3.5;
tube_bottom_z    = 3.0;

// --- Dimensiones del Bloque Base ---
// Ampliado a 30 mm para acomodar los 25.4 mm de la placa AS7341
base_width_x     = 30.0;  // Cara frontal/posterior (ancho)
base_depth_y     = 26.0;  // Eje del sensor (profundidad)
base_height      = 35.0;  // Altura total
corner_radius    = 3.0;

// --- Parámetros Ópticos ---
optical_z        = 9.0;   // Altura Z del centro de lectura en el líquido
pinhole_dia      = 2.0;   // Orificio colimador interno

// --- Parámetros LED (Eje X) ---
led_dia          = 3.2;   // Para LED estándar de 3 mm
led_depth        = 7.0;

// --- Parámetros Adafruit AS7341 ---
as_pcb_w         = 26.0;  // Ancho con holgura (nominal 25.4 mm)
as_pcb_h         = 18.4;  // Alto con holgura (nominal 17.8 mm)
as_pocket_depth  = 3.0;   // Profundidad para encastrar PCB + componentes
hole_pitch_x     = 20.32; // Distancia entre tornillos eje X (0.8")
hole_pitch_z     = 12.70; // Distancia entre tornillos eje Z (0.5")
mount_screw_dia  = 2.2;   // Agujero para tornillo M2 / M2.5 directo en plástico
mount_screw_len  = 6.0;   // Profundidad del tornillo

tube_center_x    = base_width_x / 2;
tube_center_y    = 15.0;  // Posición del tubo desplazada para optimizar óptica

// --- Renderizado ---
fluorimetro_as7341();

// ==================== MÓDULO PRINCIPAL ====================

module fluorimetro_as7341() {
    difference() {
        // 1. Bloque principal
        rounded_cube([base_width_x, base_depth_y, base_height], corner_radius);

        // 2. Cavidad interior del microtubo
        translate([tube_center_x, tube_center_y, 0]) {
            // Cono inferior
            translate([0, 0, tube_bottom_z])
                cylinder(h = cone_height, d1 = cone_tip_dia, d2 = tube_body_dia);

            // Cilindro medio
            translate([0, 0, tube_bottom_z + cone_height])
                cylinder(h = cylinder_height + 0.1, d = tube_body_dia);

            // Reborde superior
            translate([0, 0, base_height - rim_depth])
                cylinder(h = rim_depth + 1, d = rim_dia);

            // Chaflán de inserción
            translate([0, 0, base_height - 1.0])
                cylinder(h = 1.1, d1 = rim_dia, d2 = rim_dia + 2.0);

            // Orificio de drenaje / expulsión
            translate([0, 0, -1])
                cylinder(h = tube_bottom_z + 2, d = 2.5);
        }

        // 3. EJE X: Canal de Excitación (LED 3 mm)
        // Desde cara X=0 hacia el centro del tubo
        translate([-1, tube_center_y, optical_z])
            rotate([0, 90, 0])
                cylinder(h = tube_center_x + 1, d = pinhole_dia);

        // Alojamiento exterior para insertar el LED
        translate([-1, tube_center_y, optical_z])
            rotate([0, 90, 0])
                cylinder(h = led_depth + 1, d = led_dia);

        // 4. EJE Y: Canal Óptico a 90° hacia el Sensor AS7341
        // Pinhole desde el tubo hacia la cara externa Y=0
        translate([tube_center_x, -1, optical_z])
            rotate([-90, 0, 0])
                cylinder(h = tube_center_y + 1, d = pinhole_dia);

        // 5. CAVIDAD PARA LA PLACA ADAFRUIT AS7341 (Cara Y=0)
        // Bolsillo principal de la placa
        translate([tube_center_x - as_pcb_w/2, -0.1, optical_z - as_pcb_h/2])
            cube([as_pcb_w, as_pocket_depth + 0.1, as_pcb_h]);

        // Rebajes laterales para conectores STEMMA QT (evita que choquen los bordes)
        translate([tube_center_x - (as_pcb_w + 3)/2, -0.1, optical_z - 3.5])
            cube([as_pcb_w + 3, as_pocket_depth + 0.1, 7.0]);

        // Rebaje inferior para los pines soldados (headers hembra/macho)
        translate([tube_center_x - 9.0, -0.1, optical_z - as_pcb_h/2 - 2.0])
            cube([18.0, as_pocket_depth + 0.1, 4.0]);

        // 6. Agujeros de fijación M2 / M2.5 para la placa
        for (dx = [-hole_pitch_x/2, hole_pitch_x/2]) {
            for (dz = [-hole_pitch_z/2, hole_pitch_z/2]) {
                translate([tube_center_x + dx, as_pocket_depth - 0.1, optical_z + dz])
                    rotate([-90, 0, 0])
                        cylinder(h = mount_screw_len, d = mount_screw_dia);
            }
        }
    }
}

// Bloque redondeado auxiliar
module rounded_cube(size, r) {
    x = size[0];
    y = size[1];
    z = size[2];
    hull() {
        translate([r, r, 0])         cylinder(h = z, r = r);
        translate([x - r, r, 0])     cylinder(h = z, r = r);
        translate([r, y - r, 0])     cylinder(h = z, r = r);
        translate([x - r, y - r, 0]) cylinder(h = z, r = r);
    }
}