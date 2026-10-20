import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 2026
RUTA_CSV = Path(__file__).resolve().parent / "datos.csv"

SUCURSALES = {
    "San Salvador": {"cobertura": 0.97, "factor_stock": 1.45},
    "Santa Ana": {"cobertura": 0.86, "factor_stock": 1.05},
    "San Miguel": {"cobertura": 0.84, "factor_stock": 1.00},
    "La Libertad": {"cobertura": 0.78, "factor_stock": 0.85},
    "Sonsonate": {"cobertura": 0.72, "factor_stock": 0.70},
}

PROVEEDORES = [
    "Distribuidora Cuscatlán",
    "Importadora del Pacífico",
    "Grupo Comercial Lempa",
    "Suministros de Oriente",
    "Mayoreo Centroamericano",
]

CATALOGO_BASE = {
    "Abarrotes": {
        "stock": (60, 260),
        "minimo": (30, 60),
        "productos": [
            ("Arroz blanco 5 lb", 4.25), ("Frijol rojo seda 2 lb", 2.60),
            ("Azúcar blanca 5 lb", 3.40), ("Aceite vegetal 1 L", 3.15),
            ("Café molido 400 g", 5.75), ("Harina de maíz 2 lb", 1.95),
            ("Pasta espagueti 500 g", 1.10), ("Leche en polvo 800 g", 8.90),
            ("Sal yodada 1 kg", 0.65), ("Atún en agua 140 g", 1.45),
        ],
    },
    "Bebidas": {
        "stock": (50, 220),
        "minimo": (25, 50),
        "productos": [
            ("Agua purificada 1.5 L", 0.85), ("Gaseosa 2 L", 1.95),
            ("Jugo de naranja 1 L", 2.35), ("Bebida energética 473 ml", 2.10),
            ("Té frío 500 ml", 1.15), ("Horchata en polvo 400 g", 3.25),
            ("Café instantáneo 200 g", 6.40),
        ],
    },
    "Higiene Personal": {
        "stock": (40, 180),
        "minimo": (20, 40),
        "productos": [
            ("Jabón de tocador 3 un.", 2.45), ("Champú 400 ml", 4.80),
            ("Pasta dental 150 ml", 2.75), ("Desodorante 50 ml", 3.95),
            ("Papel higiénico 12 rollos", 6.50), ("Toallas húmedas 80 un.", 3.20),
            ("Cepillo dental", 1.60),
        ],
    },
    "Hogar": {
        "stock": (20, 110),
        "minimo": (10, 25),
        "productos": [
            ("Juego de sartenes 3 pzs", 34.90), ("Vajilla 16 piezas", 42.50),
            ("Detergente en polvo 2 kg", 7.80), ("Desinfectante 1 gal", 6.25),
            ("Escoba de cerdas", 4.50), ("Cortina de baño", 9.90),
            ("Juego de sábanas matrimonial", 27.00), ("Almohada estándar", 11.50),
        ],
    },
    "Ferretería": {
        "stock": (10, 90),
        "minimo": (6, 18),
        "productos": [
            ("Martillo de uña 16 oz", 9.75), ("Juego de destornilladores", 14.50),
            ("Taladro percutor 600 W", 68.00), ("Cinta métrica 5 m", 5.40),
            ("Pintura látex 1 gal", 22.90), ("Extensión eléctrica 5 m", 8.25),
            ("Candado de seguridad", 11.30), ("Foco LED 12 W", 2.95),
        ],
    },
    "Electrónica": {
        "stock": (4, 45),
        "minimo": (3, 10),
        "productos": [
            ("Audífonos Bluetooth", 29.90), ("Parlante portátil", 45.00),
            ("Cargador USB-C 25 W", 15.50), ("Mouse inalámbrico", 12.90),
            ("Memoria USB 64 GB", 9.95), ("Router WiFi doble banda", 54.00),
            ("Tablet 10 pulgadas", 189.00), ("Smartphone gama media", 279.00),
            ("Smart TV 43 pulgadas", 349.00),
        ],
    },
    "Electrodomésticos": {
        "stock": (2, 30),
        "minimo": (2, 6),
        "productos": [
            ("Licuadora 600 W", 49.90), ("Microondas 0.9 pies", 99.00),
            ("Refrigeradora 10 pies", 489.00), ("Lavadora 18 lb", 429.00),
            ("Cafetera 12 tazas", 32.50), ("Plancha de vapor", 24.90),
            ("Ventilador de pedestal", 39.90), ("Olla arrocera 1.8 L", 29.00),
            ("Cocina de gas 4 quemadores", 259.00),
        ],
    },
}


class GeneradorInventario:
    def __init__(self, semilla=SEMILLA):
        self.rng = np.random.default_rng(semilla)
        self.fecha_corte = date(2026, 10, 15)

    def construir_catalogo(self):
        filas = []
        correlativo = 1
        for categoria, config in CATALOGO_BASE.items():
            for nombre, precio_base in config["productos"]:
                n_proveedores = int(self.rng.integers(4, 6))
                proveedores = self.rng.choice(PROVEEDORES, size=n_proveedores, replace=False)
                for proveedor in proveedores:
                    variacion = self.rng.uniform(0.90, 1.12)
                    filas.append({
                        "ID_Producto": f"PRD-{correlativo:04d}",
                        "Producto": nombre,
                        "Categoria": categoria,
                        "Proveedor": str(proveedor),
                        "Precio_Unitario": round(precio_base * variacion, 2),
                        "Stock_Minimo": int(self.rng.integers(*config["minimo"])),
                    })
                    correlativo += 1
        return pd.DataFrame(filas)

    def generar(self):
        catalogo = self.construir_catalogo()
        registros = []
        for _, producto in catalogo.iterrows():
            rango = CATALOGO_BASE[producto["Categoria"]]["stock"]
            for sucursal, config in SUCURSALES.items():
                if self.rng.random() > config["cobertura"]:
                    continue
                cantidad = self.rng.integers(*rango) * config["factor_stock"]
                if self.rng.random() < 0.12:
                    cantidad = self.rng.integers(0, producto["Stock_Minimo"])
                dias_atras = int(self.rng.gamma(shape=2.0, scale=22.0))
                if self.rng.random() < 0.06:
                    dias_atras += int(self.rng.integers(90, 160))
                fecha = self.fecha_corte - timedelta(days=dias_atras)
                registros.append({
                    "ID_Producto": producto["ID_Producto"],
                    "Producto": producto["Producto"],
                    "Categoria": producto["Categoria"],
                    "Sucursal": sucursal,
                    "Proveedor": producto["Proveedor"],
                    "Cantidad": int(round(cantidad)),
                    "Precio_Unitario": producto["Precio_Unitario"],
                    "Stock_Minimo": int(producto["Stock_Minimo"]),
                    "Fecha_Ultimo_Ingreso": fecha.isoformat(),
                })
        inventario = pd.DataFrame(registros)
        return inventario.sort_values(["Sucursal", "ID_Producto"]).reset_index(drop=True)

    @staticmethod
    def guardar(df, ruta=RUTA_CSV):
        df.to_csv(ruta, index=False, encoding="utf-8")
        return ruta


class InspectorInventario:
    def __init__(self, df):
        self.df = df.copy()
        self.df["Fecha_Ultimo_Ingreso"] = pd.to_datetime(self.df["Fecha_Ultimo_Ingreso"])
        self.df["Valor_Inventario"] = (self.df["Cantidad"] * self.df["Precio_Unitario"]).round(2)

    @staticmethod
    def titulo(texto):
        print("\n" + "=" * 78)
        print(f" {texto}")
        print("=" * 78)

    def estructura(self):
        self.titulo("1. ESTRUCTURA DEL DATASET")
        filas, columnas = self.df.shape
        print(f"Registros: {filas} | Columnas: {columnas}")
        print(f"Columnas: {list(self.df.columns)}")
        self.titulo("Primeros registros - head()")
        print(self.df.head(10).to_string())
        self.titulo("Últimos registros - tail()")
        print(self.df.tail(5).to_string())
        self.titulo("Muestra aleatoria - sample()")
        print(self.df.sample(5, random_state=SEMILLA).to_string())

    def tipos_de_datos(self):
        self.titulo("2. TIPOS DE DATOS - info() y dtypes")
        self.df.info()
        print()
        print(self.df.dtypes.to_string())

    def calidad(self):
        self.titulo("3. CALIDAD DE DATOS")
        print("Valores nulos por columna - isnull().sum():")
        print(self.df.isnull().sum().to_string())
        print(f"\nFilas duplicadas - duplicated(): {int(self.df.duplicated().sum())}")
        duplicados_clave = self.df.duplicated(subset=["ID_Producto", "Sucursal"]).sum()
        print(f"Duplicados por (ID_Producto, Sucursal): {int(duplicados_clave)}")
        print("\nValores únicos por columna - nunique():")
        print(self.df.nunique().to_string())
        print(f"\nCantidades negativas: {int((self.df['Cantidad'] < 0).sum())}")
        print(f"Precios no positivos: {int((self.df['Precio_Unitario'] <= 0).sum())}")
        print(f"Memoria utilizada: {self.df.memory_usage(deep=True).sum() / 1024:.1f} KB")

    def estadisticas(self):
        self.titulo("4. ESTADÍSTICAS DESCRIPTIVAS - describe()")
        numericas = ["Cantidad", "Precio_Unitario", "Stock_Minimo", "Valor_Inventario"]
        print(self.df[numericas].describe().round(2).to_string())
        self.titulo("Variables categóricas - describe()")
        print(self.df.select_dtypes(exclude=["number", "datetime"]).describe().to_string())
        self.titulo("Fechas de último ingreso")
        fechas = self.df["Fecha_Ultimo_Ingreso"]
        print(f"Mínima: {fechas.min().date()} | Máxima: {fechas.max().date()} | Mediana: {fechas.median().date()}")
        print("\nMediana, varianza, asimetría y curtosis:")
        resumen = pd.DataFrame({
            "mediana": self.df[numericas].median(),
            "varianza": self.df[numericas].var(),
            "asimetria": self.df[numericas].skew(),
            "curtosis": self.df[numericas].kurt(),
        })
        print(resumen.round(2).to_string())
        print("\nCorrelación entre variables numéricas - corr():")
        print(self.df[numericas].corr().round(3).to_string())

    def distribuciones(self):
        self.titulo("5. DISTRIBUCIÓN DE VARIABLES CATEGÓRICAS - value_counts()")
        for columna in ["Sucursal", "Categoria", "Proveedor"]:
            conteo = self.df[columna].value_counts()
            porcentaje = self.df[columna].value_counts(normalize=True).mul(100).round(1)
            print(f"\n{columna}:")
            print(pd.DataFrame({"registros": conteo, "%": porcentaje}).to_string())

    def agregaciones(self):
        self.titulo("6. RESUMEN POR SUCURSAL - groupby()")
        por_sucursal = self.df.groupby("Sucursal").agg(
            productos=("ID_Producto", "nunique"),
            unidades=("Cantidad", "sum"),
            valor_total=("Valor_Inventario", "sum"),
            precio_promedio=("Precio_Unitario", "mean"),
        ).sort_values("valor_total", ascending=False)
        por_sucursal["%_valor"] = (por_sucursal["valor_total"] / por_sucursal["valor_total"].sum() * 100)
        print(por_sucursal.round(2).to_string())

        self.titulo("RESUMEN POR CATEGORÍA - groupby()")
        por_categoria = self.df.groupby("Categoria").agg(
            registros=("ID_Producto", "count"),
            unidades=("Cantidad", "sum"),
            valor_total=("Valor_Inventario", "sum"),
            precio_promedio=("Precio_Unitario", "mean"),
        ).sort_values("valor_total", ascending=False)
        por_categoria["%_unidades"] = por_categoria["unidades"] / por_categoria["unidades"].sum() * 100
        por_categoria["%_valor"] = por_categoria["valor_total"] / por_categoria["valor_total"].sum() * 100
        print(por_categoria.round(2).to_string())

        self.titulo("VALOR DE INVENTARIO SUCURSAL x CATEGORÍA - pivot_table()")
        tabla = pd.pivot_table(
            self.df, values="Valor_Inventario", index="Categoria",
            columns="Sucursal", aggfunc="sum", margins=True, margins_name="Total",
        )
        print(tabla.round(2).to_string())

        self.titulo("RESUMEN POR PROVEEDOR - groupby()")
        por_proveedor = self.df.groupby("Proveedor").agg(
            registros=("ID_Producto", "count"),
            valor_total=("Valor_Inventario", "sum"),
        ).sort_values("valor_total", ascending=False)
        por_proveedor["%_valor"] = por_proveedor["valor_total"] / por_proveedor["valor_total"].sum() * 100
        print(por_proveedor.round(2).to_string())

    def alertas(self):
        self.titulo("7. ALERTAS DE INVENTARIO")
        bajo = self.df[self.df["Cantidad"] < self.df["Stock_Minimo"]]
        agotado = self.df[self.df["Cantidad"] == 0]
        print(f"Registros bajo stock mínimo: {len(bajo)} ({len(bajo) / len(self.df) * 100:.1f}%)")
        print(f"Registros agotados (cantidad = 0): {len(agotado)}")
        print("\nBajo stock mínimo por sucursal:")
        print(bajo["Sucursal"].value_counts().to_string())
        print("\nBajo stock mínimo por categoría:")
        print(bajo["Categoria"].value_counts().to_string())

        corte = self.df["Fecha_Ultimo_Ingreso"].max()
        dias = (corte - self.df["Fecha_Ultimo_Ingreso"]).dt.days
        lento = self.df[dias > 90]
        print(f"\nRegistros sin ingreso en más de 90 días: {len(lento)} "
              f"(valor inmovilizado: ${lento['Valor_Inventario'].sum():,.2f})")
        print(lento.groupby("Sucursal")["Valor_Inventario"].agg(["count", "sum"]).round(2).to_string())

        self.titulo("TOP 10 REGISTROS CON MAYOR VALOR - nlargest()")
        print(self.df.nlargest(10, "Valor_Inventario")[
            ["ID_Producto", "Producto", "Sucursal", "Cantidad", "Precio_Unitario", "Valor_Inventario"]
        ].to_string(index=False))

    def ejecutar(self):
        self.estructura()
        self.tipos_de_datos()
        self.calidad()
        self.estadisticas()
        self.distribuciones()
        self.agregaciones()
        self.alertas()


def main():
    try:
        generador = GeneradorInventario()
        inventario = generador.generar()
        ruta = generador.guardar(inventario)
        print(f"Inventario generado: {ruta} ({len(inventario)} registros)")
        InspectorInventario(pd.read_csv(ruta)).ejecutar()
    except PermissionError:
        print("No se pudo escribir datos.csv: el archivo está abierto en otro programa.", file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        print(f"Error inesperado: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
