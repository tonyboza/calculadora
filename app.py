from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Base de datos de vehículos (ampliable)
vehiculos_db = {
    "audi": {
        "A1": {"largo": 3.98, "ancho": 1.75, "alto": 1.42, "factor": 1.2},
        "A3": {"largo": 4.34, "ancho": 1.82, "alto": 1.43, "factor": 1.3},
        "A4": {"largo": 4.76, "ancho": 1.84, "alto": 1.43, "factor": 1.3},
        "A6": {"largo": 4.94, "ancho": 1.89, "alto": 1.47, "factor": 1.4}
    },
    "bmw": {
        "Serie 1": {"largo": 4.32, "ancho": 1.77, "alto": 1.42, "factor": 1.2},
        "Serie 3": {"largo": 4.63, "ancho": 1.82, "alto": 1.43, "factor": 1.3},
        "Serie 5": {"largo": 4.96, "ancho": 1.87, "alto": 1.47, "factor": 1.4},
        "X5": {"largo": 4.92, "ancho": 2.00, "alto": 1.77, "factor": 1.6}
    },
    "mercedes": {
        "Clase A": {"largo": 4.30, "ancho": 1.79, "alto": 1.43, "factor": 1.2},
        "Clase C": {"largo": 4.69, "ancho": 1.81, "alto": 1.44, "factor": 1.3},
        "Clase E": {"largo": 4.93, "ancho": 1.85, "alto": 1.47, "factor": 1.4}
    }
}

# Tipos de vinilo disponibles
materiales = {
    "standard": {"precio": 15, "descripcion": "Vinilo estándar"},
    "premium": {"precio": 25, "descripcion": "Vinilo premium"},
    "cambio_color": {"precio": 30, "descripcion": "Cambio de color"},
    "personalizado": {"precio": 35, "descripcion": "Diseño personalizado"}
}

@app.route('/')
def home():
    return render_template('calculadora.html', marcas=list(vehiculos_db.keys()))

@app.route('/modelos/<marca>')
def get_modelos(marca):
    if marca in vehiculos_db:
        return jsonify(list(vehiculos_db[marca].keys()))
    return jsonify([])

@app.route('/calcular', methods=['POST'])
def calcular():
    data = request.get_json()
    
    try:
        marca = data['marca']
        modelo = data['modelo']
        tipo_vinil = data['tipo_vinil']
        horas = float(data['horas'])
        tarifa = float(data['tarifa'])
        factor_extra = float(data.get('factor_extra', 1.0))
        
        # Obtener datos del vehículo
        vehiculo = vehiculos_db[marca][modelo]
        
        # Calcular área
        area = calcular_area_vehiculo(vehiculo) * factor_extra
        
        # Calcular costos
        precio_m2 = materiales[tipo_vinil]['precio']
        coste_material = area * precio_m2
        coste_mano_obra = horas * tarifa
        total = coste_material + coste_mano_obra
        
        return jsonify({
            'success': True,
            'resultados': {
                'area': round(area, 2),
                'coste_material': round(coste_material, 2),
                'coste_mano_obra': round(coste_mano_obra, 2),
                'total': round(total, 2),
                'descripcion_material': materiales[tipo_vinil]['descripcion'],
                'metros_lineales': round(area / 1.52, 2)  # Asumiendo ancho estándar de 1.52m
            },
            'vehiculo': {
                'marca': marca,
                'modelo': modelo,
                'medidas': vehiculo
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def calcular_area_vehiculo(vehiculo):
    """Fórmula mejorada para calcular área superficial de un coche"""
    l, a, h = vehiculo['largo'], vehiculo['ancho'], vehiculo['alto']
    return 0.8 * (2 * (l * h + a * h) + l * a) * vehiculo['factor']

if __name__ == '__main__':
    app.run(debug=True)