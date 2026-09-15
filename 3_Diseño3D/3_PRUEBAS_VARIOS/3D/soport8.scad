/* =================================================================
   Fluorímetro Integrado + Case Arduino Mega 2560 R3 + Tapa Óptica
   - Cuello cilíndrico continuo reforzado (OD = 22 mm, ID = 15.5 mm)
   - Sin ranuras ni cortes en el anillo exterior (100% cerrado)
   - Alojamiento holgado para pestaña y bisagra del microtubo
   - Tapa redimensionada para cierre hermético suave
   ================================================================= */

$fn = 60;

// =================================================================
// 1. PARÁMETROS DEL CASE ARDUINO MEGA 2560 R3
// =================================================================
mega_pcb_w       = 101.6; 
mega_pcb_d       = 53.34; 
mega_wall        = 3.0;   
mega_floor       = 2.0;   
standoff_h       = 2.5;   

case_outer_h     = 14.0;  
case_inner_h     = case_outer_h - mega_floor; 

standoff_od      = 6.5;   
standoff_id      = 2.8;   // Para tornillo M3

clearance        = 0.8; 
case_inner_x     = mega_pcb_w + clearance * 2;
case_inner_y     = mega_pcb_d + clearance * 2;
case_outer_x     = case_inner_x + mega_wall * 2;
case_outer_y     = case_inner_y + mega_wall * 2;

mega_holes = [
    [14.0, 2.5],
    [15.2, 50.8],
    [90.2, 50.8],
    [96.5, 2.5]
];

usb_w            = 13.5;  
usb_y_pos        = 32.0;  
jack_w           = 11.5;  
jack_y_pos       = 3.0;   

// =================================================================
// 2. PARÁMETROS DEL BLOQUE ÓPTICO Y MICROTUBO 0.5 mL
// =================================================================
block_size       = 44.0;  // 44 x 44 mm
block_height     = 31.5;  // Altura del bloque
corner_radius    = 3.5;

// Microtubo de 0.5 mL
tube_body_dia     = 8.2;  // Diámetro del cuerpo recto
bottom_window_dia = 5.0;  // Ventana inferior de inspección visual
rim_dia           = 12.0; // Diámetro asiento del labio
rim_depth         = 2.0;  // Profundidad de asiento del borde

// --- Cuello superior cilíndrico reforzado y continuo ---
collar_h          = 4.0;  // Altura del cuello sobre el bloque (mm)
collar_od         = 22.0; // Diámetro exterior ampliado (mm) - pared gruesa y continua
collar_id         = 15.5; // Diámetro interior amplio (aloja bisagra y pestaña con holgura)

optical_z         = 8.5;  // Eje del haz óptico centrado en el cono
pinhole_dia       = 2.0;

tube_pos_x        = block_size / 2; // 22.0 mm
tube_pos_y        = block_size / 2; // 22.0 mm

// Placas AS7341 y Placa LED
pcb_w             = 26.0;
pcb_h             = 18.4;
pocket_depth      = 3.0;
hole_pitch_w      = 20.32;
hole_pitch_h      = 12.70;
mount_screw_dia   = 2.2;
mount_screw_len   = 4.5;

fluor_pos_x       = case_outer_x;
fluor_pos_y       = (case_outer_y - block_size) / 2;

// Parámetros de la tapa redimensionada
cap_clearance     = 0.25;  
cap_wall          = 2.0;   
cap_top_thick     = 2.2;   
knob_h            = 4.0;   
knob_dia          = 13.0;  

// =================================================================
// RENDERIZADO GENERAL
// =================================================================
fluorimetro_completo();

// Tapa hermética colocada al costado
translate([fluor_pos_x + block_size/2, -collar_od - 8, 0])
    tapa_fluorimetro();


// =================================================================
// MÓDULOS
// =================================================================

module fluorimetro_completo() {
    difference() {
        // 1. SÓLIDOS (Case + Bloque Óptico + Cuello Cilíndrico Continuo)
        union() {
            case_arduino_mega();

            translate([fluor_pos_x, fluor_pos_y, 0])
                rounded_cube([block_size, block_size, block_height], corner_radius);

            // Cuello cilíndrico sólido continuo
            translate([fluor_pos_x + tube_pos_x, fluor_pos_y + tube_pos_y, block_height])
                cylinder(h = collar_h, d = collar_od);
        }

        // 2. VACIADO INTEGRAL DEL MICROTUBO (100% Pasante y sin ranuras que corten paredes)
        translate([fluor_pos_x + tube_pos_x, fluor_pos_y + tube_pos_y, 0])
            cavidad_tubo_calibrada();

        // 3. MONTAJES ÓPTICOS A 90°
        // Montura Cara Y (Sensor AS7341)
        translate([fluor_pos_x, fluor_pos_y, 0])
            cavidad_montura();

        // Montura Cara X (Placa LED a 90°)
        translate([fluor_pos_x + block_size, fluor_pos_y, 0])
            rotate([0, 0, 90])
                cavidad_montura();
    }
}

// Perfil de revolución continuo: cono + cilindro + cámara superior amplia
module cavidad_tubo_calibrada() {
    z_bottom   = -1.0;
    z_tip      = 2.0;
    z_cone_top = 15.5;
    z_rim_seat = block_height - rim_depth;
    z_top      = block_height + collar_h + 1.0;

    rotate_extrude() {
        polygon(points = [
            [0, z_bottom],
            [bottom_window_dia / 2, z_bottom],
            [bottom_window_dia / 2, z_tip],
            [tube_body_dia / 2, z_cone_top],
            [tube_body_dia / 2, z_rim_seat],
            [rim_dia / 2, z_rim_seat],
            [rim_dia / 2, block_height - 0.5],
            [collar_id / 2, block_height - 0.5],
            [collar_id / 2, z_top],
            [0, z_top]
        ]);
    }
}

// Cavidad de montaje con rebajes de componentes y agujeros para tornillos
module cavidad_montura() {
    translate([tube_pos_x, -1, optical_z])
        rotate([-90, 0, 0])
            cylinder(h = tube_pos_y + 1, d = pinhole_dia);

    translate([tube_pos_x - pcb_w/2, -0.1, optical_z - pcb_h/2])
        cube([pcb_w, pocket_depth + 0.1, pcb_h]);

    translate([tube_pos_x - (pcb_w + 3.5)/2, -0.1, optical_z - 3.5])
        cube([pcb_w + 3.5, pocket_depth + 0.1, 7.0]);

    translate([tube_pos_x - 9.0, -0.1, optical_z - pcb_h/2 - 2.0])
        cube([18.0, pocket_depth + 0.1, 4.0]);

    for (dw = [-hole_pitch_w/2, hole_pitch_w/2]) {
        for (dh = [-hole_pitch_h/2, hole_pitch_h/2]) {
            translate([tube_pos_x + dw, pocket_depth - 0.1, optical_z + dh])
                rotate([-90, 0, 0])
                    cylinder(h = mount_screw_len, d = mount_screw_dia);
        }
    }
}

// Tapa Antifugas Redimensionada para Cuello de 22 mm
module tapa_fluorimetro() {
    cap_inner_dia = collar_od + cap_clearance * 2; // 22.5 mm interior
    cap_outer_dia = cap_inner_dia + cap_wall * 2;  // 26.5 mm exterior
    cap_inner_h   = collar_h + 1.2; 
    cap_total_h   = cap_inner_h + cap_top_thick;

    union() {
        difference() {
            cylinder(h = cap_total_h, d = cap_outer_dia);

            // Vaciado que envuelve el cuello exterior de 22 mm
            translate([0, 0, -0.1])
                cylinder(h = cap_inner_h + 0.1, d = cap_inner_dia);

            // Chaflán de inserción guiada en la boca
            translate([0, 0, -0.1])
                cylinder(h = 1.0, d1 = cap_inner_dia + 1.2, d2 = cap_inner_dia);
        }

        // Perilla de agarre superior estriada
        translate([0, 0, cap_total_h]) {
            cylinder(h = knob_h, d = knob_dia);
            for (a = [0 : 45 : 360]) {
                rotate([0, 0, a])
                    translate([knob_dia/2, 0, knob_h/2])
                        cylinder(h = knob_h, d = 1.4, center = true);
            }
        }
    }
}

// Case Arduino Mega 2560 Calibrado
module case_arduino_mega() {
    difference() {
        cube([case_outer_x, case_outer_y, case_outer_h]);

        translate([mega_wall, mega_wall, mega_floor])
            cube([case_inner_x, case_inner_y, case_inner_h + 1.0]);

        // Entrada USB Tipo B
        translate([-1, mega_wall + clearance + usb_y_pos, mega_floor + standoff_h])
            cube([mega_wall + 2, usb_w, case_outer_h]);

        // Entrada Jack DC
        translate([-1, mega_wall + clearance + jack_y_pos, mega_floor + standoff_h])
            cube([mega_wall + 2, jack_w, case_outer_h]);
    }

    for (h = mega_holes) {
        translate([mega_wall + clearance + h[0], mega_wall + clearance + h[1], mega_floor]) {
            difference() {
                cylinder(h = standoff_h, d = standoff_od);
                translate([0, 0, -0.5])
                    cylinder(h = standoff_h + 1.0, d = standoff_id);
            }
        }
    }
}

// Módulo auxiliar de redondeo
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