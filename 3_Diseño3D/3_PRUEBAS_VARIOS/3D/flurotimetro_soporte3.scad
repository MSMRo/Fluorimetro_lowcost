/* =================================================================
   Fluorímetro de Bajo Costo - Microtubo 0.5 mL (Versión Reforzada)
   Cuerpo ampliado (38 x 38 mm) con monturas robustas a 90°
   - Cara Y=0: Sensor Multiespectral Adafruit AS7341
   - Cara X=0: Placa Emisora LED 3 mm (Mismas dimensiones)
   ================================================================= */

$fn = 60;

// --- Dimensiones del Microtubo de 0.5 mL ---
tube_body_dia    = 8.4;   // Diámetro superior del cuerpo cilíndrico (mm)
cone_tip_dia     = 4.5;   // Diámetro inferior de la punta cónica (mm)
cone_height      = 12.0;  // Altura del cono inferior (mm)
cylinder_height  = 16.0;  // Altura del cuerpo cilíndrico (mm)
rim_dia          = 13.5;  // Diámetro del anillo superior y pestaña (mm)
rim_depth        = 3.5;   // Rebaje para la pestaña (mm)

// --- Dimensiones del Bloque Ampliado ---
block_size       = 38.0;  // 38 x 38 mm (ampliado para evitar cortes en esquinas)
block_height     = 38.0;  // Altura total del bloque (mm)
corner_radius    = 3.5;   // Redondeo de esquinas exteriores (mm)

// Base sólida inferior
tube_bottom_z    = 5.0;   // Altura de apoyo de la punta del tubo sobre la base (mm)

// --- Parámetros Ópticos ---
optical_z        = 11.5;  // Altura del haz óptico (centrado en la muestra líquida)
pinhole_dia      = 2.0;   // Canal óptico colimador hacia el centro del tubo

// El microtubo queda centrado con respecto a las ventanas de ambas placas:
tube_pos_x       = block_size / 2; // 19.0 mm
tube_pos_y       = block_size / 2; // 19.0 mm

// --- Dimensiones de las Placas (AS7341 y Placa LED) ---
pcb_w            = 26.0;  // Ancho de la cavidad (nominal 25.4 mm + holgura)
pcb_h            = 18.4;  // Alto de la cavidad (nominal 17.8 mm + holgura)
pocket_depth     = 3.0;   // Profundidad de encastre para el PCB
hole_pitch_w     = 20.32; // Distancia entre orificios horizontal (0.8")
hole_pitch_h     = 12.70; // Distancia entre orificios vertical (0.5")
mount_screw_dia  = 2.2;   // Diámetro para tornillo M2 o M2.5 autoterrajante
mount_screw_len  = 6.5;   // Profundidad del orificio del tornillo

// --- Renderizado Principal ---
fluorimetro_reforzado();

// ==================== MÓDULOS ====================

module fluorimetro_reforzado() {
    difference() {
        // 1. Bloque principal macizo
        rounded_cube([block_size, block_size, block_height], corner_radius);

        // 2. Cavidad central para el microtubo de 0.5 mL
        translate([tube_pos_x, tube_pos_y, 0]) {
            // Fondo cónico donde se ubica la muestra
            translate([0, 0, tube_bottom_z])
                cylinder(h = cone_height, d1 = cone_tip_dia, d2 = tube_body_dia);

            // Cilindro recto superior
            translate([0, 0, tube_bottom_z + cone_height])
                cylinder(h = cylinder_height + 0.1, d = tube_body_dia);

            // Rebaje para el anillo de cierre y pestaña
            translate([0, 0, block_height - rim_depth])
                cylinder(h = rim_depth + 1, d = rim_dia);

            // Chaflán de entrada superior
            translate([0, 0, block_height - 1.2])
                cylinder(h = 1.3, d1 = rim_dia, d2 = rim_dia + 2.5);

            // Orificio pasante de desagüe / expulsión por la base
            translate([0, 0, -1])
                cylinder(h = tube_bottom_z + 2, d = 2.5);
        }

        // 3. Montura A: Cara Y=0 (para el sensor Adafruit AS7341)
        cavidad_montura();

        // 4. Montura B: Cara X=0 (a 90°, para la placa emisora del LED)
        translate([0, 0, 0])
            rotate([0, 0, -90])
                translate([-block_size, 0, 0])
                    cavidad_montura();
    }
}

// Cavidad de montaje con rebajes de componentes y agujeros para tornillos
module cavidad_montura() {
    // Canal óptico directo hacia el centro del tubo
    translate([tube_pos_x, -1, optical_z])
        rotate([-90, 0, 0])
            cylinder(h = tube_pos_y + 1, d = pinhole_dia);

    // Encastre rectangular para el cuerpo del PCB
    translate([tube_pos_x - pcb_w/2, -0.1, optical_z - pcb_h/2])
        cube([pcb_w, pocket_depth + 0.1, pcb_h]);

    // Despeje lateral para conectores STEMMA QT / terminales de cable
    translate([tube_pos_x - (pcb_w + 3.5)/2, -0.1, optical_z - 3.5])
        cube([pcb_w + 3.5, pocket_depth + 0.1, 7.0]);

    // Despeje inferior para soldaduras de la tira de pines (headers)
    translate([tube_pos_x - 9.0, -0.1, optical_z - pcb_h/2 - 2.0])
        cube([18.0, pocket_depth + 0.1, 4.0]);

    // 4 Agujeros para atornillar la placa (M2 / M2.5)
    for (dw = [-hole_pitch_w/2, hole_pitch_w/2]) {
        for (dh = [-hole_pitch_h/2, hole_pitch_h/2]) {
            translate([tube_pos_x + dw, pocket_depth - 0.1, optical_z + dh])
                rotate([-90, 0, 0])
                    cylinder(h = mount_screw_len, d = mount_screw_dia);
        }
    }
}

// Bloque exterior con esquinas verticales redondeadas
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