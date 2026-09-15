/* =================================================================
   Soporte Óptico para Fluorímetro (Microtubo 1.5 mL)
   - Estructura central, cuello y cavidad del tubo intactos
   - Cara del sensor AS7341 calibrada con desahogos pasantes para cables Qwiic
   - Cara del LED a 90° independiente
   - Tapa separada a distancia segura de impresión
   ================================================================= */

$fn = 60;

// --- Dimensiones del Bloque Base ---
block_w          = 42.0;  // Eje X
block_d          = 42.0;  // Eje Y
block_h          = 40.0;  // Altura calibrada al tubo de 1.5 mL
corner_r         = 3.5;

// Centro del microtubo
cx = block_w / 2; // 21.0 mm
cy = block_d / 2; // 21.0 mm

// --- Dimensiones del Microtubo de 1.5 mL ---
tube_body_dia     = 11.2; 
cone_tip_dia      = 4.8;  
cone_h            = 18.0; 
bottom_hole_dia   = 5.0;  
rim_seat_dia      = 15.0; 
rim_seat_depth    = 2.5;  

// Cuello superior cilíndrico
collar_h          = 4.5;
collar_od         = 22.0;
collar_id         = 15.5;

// --- Parámetros Ópticos ---
optical_z         = 10.5; // Altura del haz óptico
optic_hole_dia    = 3.6;  // Apertura central ampliada

// --- Montura Cara Sensor AS7341 (Cara Y=0) ---
as_pocket_w       = 27.5; // Ancho del receptáculo (holgura para PCB nominal 25.4 mm)
as_pocket_h       = 19.5; // Altura del receptáculo (holgura para PCB nominal 17.8 mm)
as_pocket_depth   = 3.2;  // Profundidad de asiento del PCB
hole_pitch_w      = 20.32;// Distancia entre tornillos M2/M2.5 horizontal (0.8")
hole_pitch_h      = 12.70;// Distancia entre tornillos vertical (0.5")
mount_screw_dia   = 2.2;
mount_screw_len   = 5.0;

// Desahogo amplio pasante para conectores y cables Qwiic / STEMMA QT
qwiic_slot_w      = 9.5;  // Altura de paso para conector JST-SH
qwiic_total_span  = 44.0; // Pasa de lado a lado cortando hacia el exterior
qwiic_depth       = 6.5;  // Profundidad para que el conector no choque la pared

// Desahogo frontal para componentes SMD y sensor central AS7341
smd_relief_w      = 11.0; 
smd_relief_h      = 8.5;
smd_relief_depth  = 1.5;  // Rebaje extra en el fondo

// --- Montura Cara LED (Cara X=0) ---
led_pocket_w      = 26.0;
led_pocket_h      = 18.4;
led_pocket_depth  = 3.0;

// --- Parámetro de Separación de la Tapa ---
distancia_tapa_x  = block_w + 25.0; // 67.0 mm (holgura cómoda sin interferencia)


// ==================== RENDERIZADO ====================
soporte_fluorimetro_1_5ml();

// Tapa hermética reubicada con mayor separación
translate([distancia_tapa_x, cy, 0])
    tapa_estanca();


// ==================== MÓDULOS ====================

module soporte_fluorimetro_1_5ml() {
    difference() {
        // 1. Bloque base sólido + cuello cilíndrico
        union() {
            rounded_cube([block_w, block_d, block_h], corner_r);

            translate([cx, cy, block_h])
                cylinder(h = collar_h, d = collar_od);
        }

        // 2. Vaciado interior continuo del microtubo de 1.5 mL
        translate([cx, cy, 0])
            cavidad_microtubo_1_5ml();

        // 3. Montura Cara Y=0: Sensor AS7341 con desahogos pasantes Qwiic
        cavidad_sensor_as7341();

        // 4. Montura Cara X=0: Placa LED estándar a 90°
        cavidad_modulo_led();
    }
}

// Cavidad de revolución 100% pasante para microtubo de 1.5 mL
module cavidad_microtubo_1_5ml() {
    z_floor    = -1.0;
    z_cone_end = 19.0;
    z_rim      = block_h - rim_seat_depth;
    z_exit     = block_h + collar_h + 1.0;

    rotate_extrude() {
        polygon(points = [
            [0, z_floor],
            [bottom_hole_dia / 2, z_floor],
            [bottom_hole_dia / 2, 2.0],
            [tube_body_dia / 2, z_cone_end],
            [tube_body_dia / 2, z_rim],
            [rim_seat_dia / 2, z_rim],
            [rim_seat_dia / 2, block_h],
            [collar_id / 2, block_h],
            [collar_id / 2, z_exit],
            [0, z_exit]
        ]);
    }
}

// Montura para Adafruit AS7341 (Cara Y=0)
module cavidad_sensor_as7341() {
    // Canal óptico hacia el microtubo
    translate([cx, -1.0, optical_z])
        rotate([-90, 0, 0])
            cylinder(h = cy + 1.0, d = optic_hole_dia);

    // Encastre principal para el PCB (con holgura de 27.5 mm)
    translate([cx - as_pocket_w/2, -0.1, optical_z - as_pocket_h/2])
        cube([as_pocket_w, as_pocket_depth + 0.1, as_pocket_h]);

    // Ranuras pasantes laterales continuas para los conectores y cables Qwiic
    translate([cx - qwiic_total_span/2, -0.1, optical_z - qwiic_slot_w/2])
        cube([qwiic_total_span, qwiic_depth, qwiic_slot_w]);

    // Rebaje de alivio para componentes SMD centrales
    translate([cx - smd_relief_w/2, as_pocket_depth - 0.1, optical_z - smd_relief_h/2])
        cube([smd_relief_w, smd_relief_depth + 0.1, smd_relief_h]);

    // Rebaje inferior para pines soldados
    translate([cx - 9.0, -0.1, optical_z - as_pocket_h/2 - 2.5])
        cube([18.0, as_pocket_depth + 0.1, 4.0]);

    // 4 orificios para tornillos de fijación M2 / M2.5
    for (dx = [-hole_pitch_w/2, hole_pitch_w/2]) {
        for (dz = [-hole_pitch_h/2, hole_pitch_h/2]) {
            translate([cx + dx, as_pocket_depth - 0.1, optical_z + dz])
                rotate([-90, 0, 0])
                    cylinder(h = mount_screw_len, d = mount_screw_dia);
        }
    }
}

// Montura Cara X=0 para la Placa LED
module cavidad_modulo_led() {
    rotate([0, 0, -90])
        translate([-block_w, 0, 0]) {
            // Canal óptico de emisión
            translate([cx, -1.0, optical_z])
                rotate([-90, 0, 0])
                    cylinder(h = cy + 1.0, d = optic_hole_dia);

            // Bolsillo del PCB
            translate([cx - led_pocket_w/2, -0.1, optical_z - led_pocket_h/2])
                cube([led_pocket_w, led_pocket_depth + 0.1, led_pocket_h]);

            // Ranuras laterales
            translate([cx - (led_pocket_w + 6.0)/2, -0.1, optical_z - 3.5])
                cube([led_pocket_w + 6.0, led_pocket_depth + 1.0, 7.0]);

            // Desahogo inferior
            translate([cx - 9.0, -0.1, optical_z - led_pocket_h/2 - 2.0])
                cube([18.0, led_pocket_depth + 0.1, 3.5]);

            // Orificios para tornillos M2 / M2.5
            for (dx = [-hole_pitch_w/2, hole_pitch_w/2]) {
                for (dz = [-hole_pitch_h/2, hole_pitch_h/2]) {
                    translate([cx + dx, led_pocket_depth - 0.1, optical_z + dz])
                        rotate([-90, 0, 0])
                            cylinder(h = mount_screw_len, d = mount_screw_dia);
                }
            }
        }
}

// Tapa estanca a la luz
module tapa_estanca() {
    cap_clearance = 0.25;
    cap_wall      = 2.0;
    cap_inner_dia = collar_od + cap_clearance * 2;
    cap_outer_dia = cap_inner_dia + cap_wall * 2;
    cap_inner_h   = collar_h + 1.5;
    cap_total_h   = cap_inner_h + 2.0;

    union() {
        difference() {
            cylinder(h = cap_total_h, d = cap_outer_dia);

            translate([0, 0, -0.1])
                cylinder(h = cap_inner_h + 0.1, d = cap_inner_dia);

            translate([0, 0, -0.1])
                cylinder(h = 1.0, d1 = cap_inner_dia + 1.5, d2 = cap_inner_dia);
        }

        // Tirador estriado superior
        translate([0, 0, cap_total_h]) {
            cylinder(h = 4.0, d = 12.0);
            for (a = [0 : 60 : 360]) {
                rotate([0, 0, a])
                    translate([6.0, 0, 2.0])
                        cylinder(h = 4.0, d = 1.2, center = true);
            }
        }
    }
}

// Cubo redondeado auxiliar
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