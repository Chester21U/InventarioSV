import html
import io
import sys
from pathlib import Path

import matplotlib
import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QSettings, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QFont, QKeySequence
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QTableView, QTabWidget, QToolTip,
    QVBoxLayout, QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter

matplotlib.rcParams["text.parse_math"] = False

RUTA_DATOS = Path(__file__).resolve().parent / "datos.csv"
TODAS = "Todas"
ORDEN_SUCURSALES = ["San Salvador", "Santa Ana", "San Miguel", "La Libertad", "Sonsonate"]
ORDEN_CATEGORIAS = [
    "Abarrotes", "Bebidas", "Higiene Personal", "Hogar", "Ferretería", "Electrónica", "Electrodomésticos",
]
ESTADOS = ["Todos", "Normal", "Con alerta", "Bajo mínimo", "Agotado"]
PATRONES = ["", "///", "\\\\\\", "xxx", "...", "|||", "---"]

TEMAS = {
    "oscuro": {
        "fondo": "#141413", "superficie": "#1a1a19", "tarjeta": "#21211f", "borde": "#34342f",
        "control": "#262624", "texto": "#ecebe6", "texto2": "#c3c2b7", "tenue": "#8f8d86",
        "grilla": "#2c2c2a", "eje": "#3a3a36", "serie": "#3987e5", "atenuado": "#3f3f3b",
        "alerta": "#e5605f", "bajo_minimo": "#ec835a", "agotado": "#d03b3b", "resalte": "#ecebe6",
        "categorias": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9"],
        "mapa": ["#1d2430", "#184f95", "#2a78d6", "#6da7ec", "#cde2fb"], "tinta_mapa": "#141413",
    },
    "claro": {
        "fondo": "#f2f1ec", "superficie": "#fafaf7", "tarjeta": "#fdfdfb", "borde": "#dcdbd4",
        "control": "#ffffff", "texto": "#1f1f1d", "texto2": "#55544f", "tenue": "#898781",
        "grilla": "#e5e4de", "eje": "#c3c2b7", "serie": "#2a78d6", "atenuado": "#d6d5cf",
        "alerta": "#c03535", "bajo_minimo": "#ec835a", "agotado": "#d03b3b", "resalte": "#1f1f1d",
        "categorias": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"],
        "mapa": ["#eef4fc", "#b7d3f6", "#5598e7", "#1c5cab", "#0d366b"], "tinta_mapa": "#ffffff",
    },
}


class Estilo:
    nombre = "oscuro"
    tema = TEMAS["oscuro"]
    patrones = False
    tamano = 10

    @classmethod
    def activar(cls, nombre):
        cls.nombre = nombre if nombre in TEMAS else "oscuro"
        cls.tema = TEMAS[cls.nombre]

    @classmethod
    def fs(cls, puntos):
        return puntos * cls.tamano / 10

    @classmethod
    def color_categoria(cls, categoria):
        if categoria in ORDEN_CATEGORIAS:
            return cls.tema["categorias"][ORDEN_CATEGORIAS.index(categoria)]
        return cls.tema["tenue"]

    @classmethod
    def patron_categoria(cls, categoria):
        if not cls.patrones or categoria not in ORDEN_CATEGORIAS:
            return ""
        return PATRONES[ORDEN_CATEGORIAS.index(categoria)]

    @classmethod
    def mapa_color(cls):
        return LinearSegmentedColormap.from_list("secuencial", cls.tema["mapa"])

    @classmethod
    def hoja_qt(cls):
        t = cls.tema
        base = cls.tamano
        return f"""
        QMainWindow, QDialog, QWidget {{ background: {t['fondo']}; color: {t['texto']}; font-size: {base}pt; }}
        QFrame#tarjeta {{ background: {t['tarjeta']}; border: 1px solid {t['borde']}; border-radius: 10px; }}
        QFrame#tarjeta:hover {{ border: 1px solid {t['serie']}; }}
        QFrame#tarjeta QLabel {{ background: transparent; }}
        QLabel#tituloTarjeta {{ color: {t['texto2']}; font-size: {base - 1}pt; }}
        QLabel#valorTarjeta {{ font-size: {base + 7}pt; font-weight: 600; }}
        QLabel#pistaTarjeta {{ color: {t['tenue']}; font-size: {base - 2}pt; }}
        QLabel#encabezado {{ font-size: {base + 5}pt; font-weight: 600; }}
        QLabel#subtitulo, QLabel#etiqueta {{ color: {t['texto2']}; background: transparent; }}
        QComboBox, QLineEdit, QSpinBox, QPushButton {{
            background: {t['control']}; color: {t['texto']}; border: 1px solid {t['borde']};
            border-radius: 6px; padding: 5px 9px; min-height: 18px; }}
        QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{ border: 1px solid {t['serie']}; }}
        QComboBox QAbstractItemView {{ background: {t['control']}; color: {t['texto']};
            selection-background-color: {t['serie']}; selection-color: #ffffff; }}
        QPushButton:hover {{ border: 1px solid {t['serie']}; }}
        QPushButton#primario {{ background: {t['serie']}; color: #ffffff; border: none; }}
        QCheckBox {{ background: transparent; spacing: 8px; }}
        QCheckBox::indicator {{ width: 15px; height: 15px; border: 1px solid {t['borde']};
            border-radius: 4px; background: {t['control']}; }}
        QCheckBox::indicator:checked {{ background: {t['serie']}; border: 1px solid {t['serie']}; }}
        QTabWidget::pane {{ border: 1px solid {t['borde']}; border-radius: 8px; background: {t['superficie']}; }}
        QWidget#pagina {{ background: {t['superficie']}; }}
        QTabBar::tab {{ background: transparent; color: {t['texto2']}; padding: 8px 14px; border: none; }}
        QTabBar::tab:selected {{ color: {t['texto']}; font-weight: 600; border-bottom: 2px solid {t['serie']}; }}
        QTabBar::tab:hover {{ color: {t['texto']}; }}
        QTableView {{ background: {t['superficie']}; alternate-background-color: {t['tarjeta']};
            gridline-color: {t['grilla']}; border: none; selection-background-color: {t['serie']};
            selection-color: #ffffff; }}
        QHeaderView::section {{ background: {t['tarjeta']}; color: {t['texto2']}; padding: 6px;
            border: none; border-bottom: 1px solid {t['borde']}; font-weight: 600; }}
        QTableCornerButton::section {{ background: {t['tarjeta']}; border: none; }}
        QPlainTextEdit {{ background: {t['superficie']}; color: {t['texto']}; border: none; }}
        QMenuBar {{ background: {t['fondo']}; color: {t['texto']}; }}
        QMenuBar::item:selected, QMenu::item:selected {{ background: {t['serie']}; color: #ffffff; }}
        QMenu {{ background: {t['tarjeta']}; color: {t['texto']}; border: 1px solid {t['borde']}; }}
        QStatusBar {{ background: {t['fondo']}; color: {t['texto2']}; }}
        QToolTip {{ background: {t['tarjeta']}; color: {t['texto']}; border: 1px solid {t['borde']};
            padding: 6px; border-radius: 6px; }}
        QScrollBar:vertical, QScrollBar:horizontal {{ background: {t['superficie']}; border: none;
            width: 10px; height: 10px; }}
        QScrollBar::handle {{ background: {t['eje']}; border-radius: 5px; min-height: 24px; min-width: 24px; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
        QToolBar {{ background: {t['superficie']}; border: none; }}
        """


def formato_dolares(valor, _=None):
    if abs(valor) >= 1_000_000:
        return f"${valor / 1_000_000:.2f}M"
    if abs(valor) >= 10_000:
        return f"${valor / 1_000:.0f}k"
    if abs(valor) >= 1_000:
        return f"${valor / 1_000:.1f}k"
    return f"${valor:,.0f}"


def formato_miles(valor, _=None):
    return f"{valor:,.0f}"


def texto_seguro(valor):
    return html.escape(str(valor))


def tooltip(valor, titulo, *detalles):
    lineas = [f"<b style='font-size:{Estilo.tamano + 2}pt'>{valor}</b>", texto_seguro(titulo)]
    lineas += [f"<span style='color:{Estilo.tema['texto2']}'>{d}</span>" for d in detalles if d]
    return "<br>".join(lineas)


class InventarioError(Exception):
    pass


class GestorInventario:
    COLUMNAS_REQUERIDAS = [
        "ID_Producto", "Producto", "Categoria", "Sucursal", "Proveedor",
        "Cantidad", "Precio_Unitario", "Stock_Minimo", "Fecha_Ultimo_Ingreso",
    ]

    def __init__(self):
        self.df = pd.DataFrame()
        self.ruta = None

    def cargar(self, ruta):
        ruta = Path(ruta)
        if not ruta.exists():
            raise InventarioError(f"No se encontró el archivo:\n{ruta}")
        try:
            df = pd.read_csv(ruta, encoding="utf-8")
        except pd.errors.EmptyDataError as error:
            raise InventarioError("El archivo CSV está vacío.") from error
        except pd.errors.ParserError as error:
            raise InventarioError(f"El archivo CSV tiene un formato inválido:\n{error}") from error
        except UnicodeDecodeError as error:
            raise InventarioError("El archivo no está codificado en UTF-8.") from error

        faltantes = [c for c in self.COLUMNAS_REQUERIDAS if c not in df.columns]
        if faltantes:
            raise InventarioError("Faltan columnas obligatorias: " + ", ".join(faltantes))
        if df.empty:
            raise InventarioError("El inventario no contiene registros.")
        nulos = df[self.COLUMNAS_REQUERIDAS].isnull().sum()
        if nulos.any():
            detalle = ", ".join(f"{c} ({n})" for c, n in nulos[nulos > 0].items())
            raise InventarioError(f"Hay valores vacíos en: {detalle}")

        try:
            df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="raise").astype(int)
            df["Precio_Unitario"] = pd.to_numeric(df["Precio_Unitario"], errors="raise").astype(float)
            df["Stock_Minimo"] = pd.to_numeric(df["Stock_Minimo"], errors="raise").astype(int)
            df["Fecha_Ultimo_Ingreso"] = pd.to_datetime(df["Fecha_Ultimo_Ingreso"], errors="raise")
        except (ValueError, TypeError) as error:
            raise InventarioError(f"Hay valores con tipo de dato incorrecto:\n{error}") from error

        for columna in ("ID_Producto", "Producto", "Categoria", "Sucursal", "Proveedor"):
            df[columna] = df[columna].astype(str).str.strip()
        corte = df["Fecha_Ultimo_Ingreso"].max()
        df["Valor_Inventario"] = (df["Cantidad"] * df["Precio_Unitario"]).round(2)
        df["Dias_Sin_Ingreso"] = (corte - df["Fecha_Ultimo_Ingreso"]).dt.days
        df["Estado_Stock"] = "Normal"
        df.loc[df["Cantidad"] < df["Stock_Minimo"], "Estado_Stock"] = "Bajo mínimo"
        df.loc[df["Cantidad"] == 0, "Estado_Stock"] = "Agotado"
        self.df = df
        self.ruta = ruta
        return df

    @property
    def cargado(self):
        return not self.df.empty

    @property
    def fecha_corte(self):
        return self.df["Fecha_Ultimo_Ingreso"].max()

    def valores(self, columna):
        presentes = list(self.df[columna].unique())
        orden = {"Sucursal": ORDEN_SUCURSALES, "Categoria": ORDEN_CATEGORIAS}.get(columna, [])
        return [v for v in orden if v in presentes] + sorted(v for v in presentes if v not in orden)

    def filtrar(self, filtros, excluir=()):
        datos = self.df
        for columna in ("Sucursal", "Categoria", "Proveedor"):
            valor = filtros.get(columna, TODAS)
            if columna not in excluir and valor != TODAS:
                datos = datos[datos[columna] == valor]
        estado = filtros.get("Estado", "Todos")
        if "Estado" not in excluir and estado != "Todos":
            if estado == "Con alerta":
                datos = datos[datos["Estado_Stock"] != "Normal"]
            else:
                datos = datos[datos["Estado_Stock"] == estado]
        texto = filtros.get("Texto", "").strip()
        if texto and "Texto" not in excluir:
            coincide = (datos["Producto"].str.contains(texto, case=False, regex=False)
                        | datos["ID_Producto"].str.contains(texto, case=False, regex=False))
            datos = datos[coincide]
        return datos

    @staticmethod
    def indicadores(datos, umbral):
        lentos = datos[datos["Dias_Sin_Ingreso"] > umbral]
        return {
            "registros": len(datos),
            "productos": datos["ID_Producto"].nunique(),
            "unidades": int(datos["Cantidad"].sum()),
            "valor": float(datos["Valor_Inventario"].sum()),
            "alertas": int((datos["Estado_Stock"] != "Normal").sum()),
            "agotados": int((datos["Estado_Stock"] == "Agotado").sum()),
            "lentos": len(lentos),
            "valor_lento": float(lentos["Valor_Inventario"].sum()),
        }

    @staticmethod
    def resumen_estadistico(datos):
        buffer = io.StringIO()
        vista = datos[GestorInventario.COLUMNAS_REQUERIDAS + ["Valor_Inventario"]]
        separador = "=" * 90
        buffer.write(f"{separador}\nESTRUCTURA\n{separador}\n")
        buffer.write(f"Registros: {vista.shape[0]}  |  Columnas: {vista.shape[1]}\n\n")
        vista.info(buf=buffer)
        buffer.write(f"\n{separador}\nVALORES NULOS Y DUPLICADOS\n{separador}\n")
        buffer.write(vista.isnull().sum().to_string())
        buffer.write(f"\n\nFilas duplicadas: {int(vista.duplicated().sum())}\n")
        buffer.write(f"\n{separador}\nESTADÍSTICAS DESCRIPTIVAS (numéricas)\n{separador}\n")
        numericas = ["Cantidad", "Precio_Unitario", "Stock_Minimo", "Valor_Inventario"]
        buffer.write(vista[numericas].describe().round(2).to_string())
        buffer.write(f"\n\n{separador}\nESTADÍSTICAS DESCRIPTIVAS (categóricas)\n{separador}\n")
        buffer.write(vista.select_dtypes(exclude=["number", "datetime"]).describe().to_string())
        if len(vista) > 1:
            buffer.write(f"\n\n{separador}\nCORRELACIÓN\n{separador}\n")
            buffer.write(vista[numericas].corr().round(3).to_string())
        for columna in ["Sucursal", "Categoria", "Proveedor"]:
            buffer.write(f"\n\n{separador}\nFRECUENCIAS: {columna.upper()}\n{separador}\n")
            buffer.write(vista[columna].value_counts().to_string())
        return buffer.getvalue()


class ModeloTabla(QAbstractTableModel):
    COLUMNAS = [
        "ID_Producto", "Producto", "Categoria", "Sucursal", "Proveedor", "Cantidad",
        "Precio_Unitario", "Stock_Minimo", "Valor_Inventario", "Fecha_Ultimo_Ingreso", "Estado_Stock",
    ]
    MONEDA = {"Precio_Unitario", "Valor_Inventario"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._df = pd.DataFrame(columns=self.COLUMNAS)

    def actualizar(self, df):
        self.beginResetModel()
        self._df = df[self.COLUMNAS].reset_index(drop=True)
        self.endResetModel()

    def fila(self, indice):
        return self._df.iloc[indice]

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNAS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        columna = self.COLUMNAS[index.column()]
        valor = self._df.iat[index.row(), index.column()]
        if role == Qt.DisplayRole:
            if columna in self.MONEDA:
                return f"${valor:,.2f}"
            if columna == "Fecha_Ultimo_Ingreso":
                return valor.strftime("%Y-%m-%d")
            if columna == "Estado_Stock" and valor != "Normal":
                return f"⚠ {valor}"
            return str(valor)
        if role == Qt.TextAlignmentRole and pd.api.types.is_number(valor):
            return int(Qt.AlignRight | Qt.AlignVCenter)
        if role == Qt.ForegroundRole and columna == "Estado_Stock" and valor != "Normal":
            return QColor(Estilo.tema["alerta"])
        if role == Qt.ToolTipRole:
            return "Doble clic para ver el detalle del producto"
        return None

    def headerData(self, seccion, orientacion, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientacion == Qt.Horizontal:
            return self.COLUMNAS[seccion].replace("_", " ")
        return str(seccion + 1)

    def sort(self, columna, orden=Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self._df = self._df.sort_values(
            self.COLUMNAS[columna], ascending=orden == Qt.AscendingOrder, kind="mergesort"
        ).reset_index(drop=True)
        self.layoutChanged.emit()


class ModeloSimple(QAbstractTableModel):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self._df = df.reset_index(drop=True)

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            valor = self._df.iat[index.row(), index.column()]
            return f"{valor:,}" if pd.api.types.is_integer(valor) else str(valor)
        return None

    def headerData(self, seccion, orientacion, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientacion == Qt.Horizontal:
            return str(self._df.columns[seccion]).replace("_", " ")
        return None


class ZonaArtista:
    def __init__(self, artista, texto, accion=None):
        self.artista = artista
        self.texto = texto
        self.accion = accion
        self.borde = artista.get_edgecolor()
        self.grosor = artista.get_linewidth()
        self.orden = artista.get_zorder()

    def consultar(self, evento):
        if evento.inaxes is not self.artista.axes:
            return None
        dentro, _ = self.artista.contains(evento)
        return (id(self.artista), self.texto, self.accion) if dentro else None

    def resaltar(self, clave, activo):
        if activo:
            self.artista.set_edgecolor(Estilo.tema["resalte"])
            self.artista.set_linewidth(2.2)
            self.artista.set_zorder(self.orden + 5)
        else:
            self.artista.set_edgecolor(self.borde)
            self.artista.set_linewidth(self.grosor)
            self.artista.set_zorder(self.orden)


class ZonaMapa:
    def __init__(self, eje, filas, columnas, texto, accion=None):
        self.eje = eje
        self.filas = filas
        self.columnas = columnas
        self.texto = texto
        self.accion = accion
        self.marco = Rectangle((0, 0), 1, 1, fill=False, edgecolor=Estilo.tema["resalte"],
                               linewidth=2.5, visible=False, zorder=10)
        eje.add_patch(self.marco)

    def consultar(self, evento):
        if evento.inaxes is not self.eje or evento.xdata is None:
            return None
        columna, fila = int(round(evento.xdata)), int(round(evento.ydata))
        if not (0 <= fila < self.filas and 0 <= columna < self.columnas):
            return None
        accion = (lambda: self.accion(fila, columna)) if self.accion else None
        return ((fila, columna), self.texto(fila, columna), accion)

    def resaltar(self, clave, activo):
        if activo:
            fila, columna = clave
            self.marco.set_xy((columna - 0.5, fila - 0.5))
        self.marco.set_visible(activo)


class LienzoInteractivo(QWidget):
    def __init__(self, filas=1, columnas=1, barra=True, parent=None):
        super().__init__(parent)
        self.setObjectName("pagina")
        self.filas = filas
        self.columnas = columnas
        self.figura = Figure(figsize=(10, 5), dpi=100, layout="constrained")
        self.canvas = FigureCanvasQTAgg(self.figura)
        self.canvas.setMouseTracking(True)
        self.barra = NavigationToolbar2QT(self.canvas, self, coordinates=False) if barra else None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        if self.barra:
            layout.addWidget(self.barra)
        layout.addWidget(self.canvas)
        self.zonas = []
        self.activa = None
        self.canvas.mpl_connect("motion_notify_event", self.al_mover)
        self.canvas.mpl_connect("button_press_event", self.al_hacer_clic)
        self.canvas.mpl_connect("figure_leave_event", self.al_salir)
        self.ejes = []
        self.reiniciar()

    def modo_navegacion(self):
        return bool(self.barra and self.barra.mode)

    def reiniciar(self, filas=None, columnas=None):
        self.figura.clear()
        self.zonas = []
        self.activa = None
        self.figura.set_facecolor(Estilo.tema["superficie"])
        filas = filas or self.filas
        columnas = columnas or self.columnas
        self.ejes = [self.figura.add_subplot(filas, columnas, i + 1) for i in range(filas * columnas)]
        for eje in self.ejes:
            self.estilizar(eje)
        return self.ejes

    @staticmethod
    def estilizar(eje):
        t = Estilo.tema
        eje.set_facecolor(t["superficie"])
        for lado in ("top", "right"):
            eje.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            eje.spines[lado].set_color(t["eje"])
        eje.tick_params(colors=t["texto2"], labelsize=Estilo.fs(9), length=0)
        eje.grid(axis="both", color=t["grilla"], linewidth=0.7)
        eje.set_axisbelow(True)

    @staticmethod
    def titulo(eje, texto):
        eje.set_title(texto, loc="left", fontsize=Estilo.fs(11.5), fontweight="bold",
                      color=Estilo.tema["texto"], pad=10)

    def registrar(self, artista, texto, accion=None):
        self.zonas.append(ZonaArtista(artista, texto, accion))

    def registrar_zona(self, zona):
        self.zonas.append(zona)

    def buscar(self, evento):
        for zona in reversed(self.zonas):
            resultado = zona.consultar(evento)
            if resultado:
                return zona, resultado
        return None, None

    def al_mover(self, evento):
        if self.modo_navegacion():
            return
        zona, resultado = self.buscar(evento)
        clave = (id(zona), resultado[0]) if resultado else None
        if clave != (self.activa[0] if self.activa else None):
            if self.activa:
                self.activa[1].resaltar(self.activa[2], False)
            self.activa = (clave, zona, resultado[0]) if resultado else None
            if resultado:
                zona.resaltar(resultado[0], True)
            self.canvas.draw_idle()
        if resultado:
            QToolTip.showText(QCursor.pos(), resultado[1], self.canvas)
            self.canvas.setCursor(Qt.PointingHandCursor if resultado[2] else Qt.CrossCursor)
        else:
            QToolTip.hideText()
            self.canvas.unsetCursor()

    def al_hacer_clic(self, evento):
        if evento.button != 1 or self.modo_navegacion():
            return
        _, resultado = self.buscar(evento)
        if resultado and resultado[2]:
            QToolTip.hideText()
            QTimer.singleShot(0, resultado[2])

    def al_salir(self, _evento):
        QToolTip.hideText()
        if self.activa:
            self.activa[1].resaltar(self.activa[2], False)
            self.activa = None
            self.canvas.draw_idle()

    def sin_datos(self, mensaje="Sin datos para los filtros seleccionados"):
        (eje,) = self.reiniciar(1, 1)
        eje.axis("off")
        eje.text(0.5, 0.5, mensaje, ha="center", va="center",
                 color=Estilo.tema["texto2"], fontsize=Estilo.fs(12))
        self.dibujar()

    def dibujar(self):
        self.canvas.draw_idle()


def leyenda_suave(eje, **opciones):
    leyenda = eje.legend(frameon=False, fontsize=Estilo.fs(8.5), **opciones)
    for texto in leyenda.get_texts():
        texto.set_color(Estilo.tema["texto2"])
    return leyenda


class GraficosInventario:
    @staticmethod
    def etiquetar_barras(eje, barras, valores, formateador, maximo):
        for barra, valor in zip(barras, valores):
            eje.text(barra.get_width() + maximo * 0.012, barra.get_y() + barra.get_height() / 2,
                     formateador(valor), va="center", fontsize=Estilo.fs(9), color=Estilo.tema["texto2"])

    @classmethod
    def barras(cls, lienzo, eje, serie, formateador, titulo, seleccion, describir, accion, colores=None):
        t = Estilo.tema
        serie = serie.sort_values()
        if colores is None:
            colores = [t["serie"] if seleccion in (None, nombre) else t["atenuado"] for nombre in serie.index]
        barras = eje.barh(serie.index, serie.values, color=colores, height=0.62,
                          edgecolor=t["superficie"], linewidth=0)
        eje.grid(axis="y", visible=False)
        eje.xaxis.set_major_formatter(FuncFormatter(formateador))
        maximo = serie.max() if len(serie) else 0
        cls.etiquetar_barras(eje, barras, serie.values, formateador, maximo)
        eje.set_xlim(0, maximo * 1.18 if maximo else 1)
        total = serie.sum()
        for barra, (nombre, valor) in zip(barras, serie.items()):
            lienzo.registrar(barra, describir(nombre, valor, total),
                             (lambda n=nombre: accion(n)) if accion else None)
        LienzoInteractivo.titulo(eje, titulo)
        return barras

    @classmethod
    def sucursales(cls, lienzo, datos, seleccion, accion):
        eje_unidades, eje_valor = lienzo.reiniciar()
        agrupado = datos.groupby("Sucursal").agg(
            unidades=("Cantidad", "sum"), valor=("Valor_Inventario", "sum"), registros=("ID_Producto", "count"))

        def describir(campo):
            def interno(nombre, valor, total):
                fila = agrupado.loc[nombre]
                principal = f"{valor:,.0f} unidades" if campo == "unidades" else f"${valor:,.2f}"
                return tooltip(principal, nombre, f"{valor / total * 100:.1f}% del total",
                               f"{int(fila['registros'])} registros", "Clic para filtrar esta sucursal")
            return interno

        cls.barras(lienzo, eje_unidades, agrupado["unidades"], formato_miles,
                   "Unidades en existencia por sucursal", seleccion, describir("unidades"), accion)
        cls.barras(lienzo, eje_valor, agrupado["valor"], formato_dolares,
                   "Valor del inventario por sucursal (USD)", seleccion, describir("valor"), accion)
        lienzo.dibujar()

    @classmethod
    def categorias(cls, lienzo, datos, seleccion, accion):
        t = Estilo.tema
        eje_dona, eje_unidades = lienzo.reiniciar()
        agrupado = datos.groupby("Categoria").agg(
            valor=("Valor_Inventario", "sum"), unidades=("Cantidad", "sum"), registros=("ID_Producto", "count"))
        orden = [c for c in ORDEN_CATEGORIAS if c in agrupado.index] + \
                [c for c in agrupado.index if c not in ORDEN_CATEGORIAS]
        agrupado = agrupado.loc[orden]
        colores = [Estilo.color_categoria(c) if seleccion in (None, c) else t["atenuado"] for c in orden]
        total = agrupado["valor"].sum()
        porciones, _ = eje_dona.pie(
            agrupado["valor"], colors=colores, startangle=90, counterclock=False,
            wedgeprops={"width": 0.38, "edgecolor": t["superficie"], "linewidth": 2},
        )
        for porcion, categoria in zip(porciones, orden):
            porcion.set_hatch(Estilo.patron_categoria(categoria))
            fila = agrupado.loc[categoria]
            lienzo.registrar(porcion, tooltip(
                f"${fila['valor']:,.2f}", categoria, f"{fila['valor'] / total * 100:.1f}% del valor",
                f"{int(fila['unidades']):,} unidades · {int(fila['registros'])} registros",
                "Clic para filtrar esta categoría"), lambda c=categoria: accion(c))
        etiquetas = [f"{c}  {v / total * 100:.1f}%" for c, v in agrupado["valor"].items()]
        leyenda_suave(eje_dona, handles=porciones, labels=etiquetas, loc="center left", bbox_to_anchor=(0.95, 0.5))
        eje_dona.text(0, 0, f"{formato_dolares(total)}\nvalor total", ha="center", va="center",
                      fontsize=Estilo.fs(11), fontweight="bold", color=t["texto"])
        eje_dona.set_aspect("equal")
        LienzoInteractivo.titulo(eje_dona, "Proporción del valor por categoría")

        def describir(nombre, valor, total_u):
            return tooltip(f"{valor:,.0f} unidades", nombre, f"{valor / total_u * 100:.1f}% de las unidades",
                           "Clic para filtrar esta categoría")

        unidades = agrupado["unidades"].sort_values()
        colores_u = [Estilo.color_categoria(c) if seleccion in (None, c) else t["atenuado"] for c in unidades.index]
        barras = cls.barras(lienzo, eje_unidades, unidades, formato_miles, "Unidades en existencia por categoría",
                            seleccion, describir, accion, colores_u)
        for barra, categoria in zip(barras, unidades.index):
            barra.set_hatch(Estilo.patron_categoria(categoria))
        lienzo.dibujar()

    @staticmethod
    def mapa_calor(lienzo, datos, metrica, accion):
        t = Estilo.tema
        (eje,) = lienzo.reiniciar()
        configuracion = {
            "Valor del inventario": ("Valor_Inventario", "sum", formato_dolares, lambda v: f"${v:,.2f}"),
            "Unidades": ("Cantidad", "sum", formato_miles, lambda v: f"{v:,.0f} unidades"),
            "Registros": ("ID_Producto", "count", formato_miles, lambda v: f"{v:,.0f} registros"),
            "Registros con alerta": ("Alerta", "sum", formato_miles, lambda v: f"{v:,.0f} con alerta"),
        }
        columna, funcion, formateador, largo = configuracion[metrica]
        base = datos.assign(Alerta=(datos["Estado_Stock"] != "Normal").astype(int))
        tabla = base.pivot_table(values=columna, index="Categoria", columns="Sucursal",
                                 aggfunc=funcion, fill_value=0)
        tabla = tabla.reindex(index=[c for c in ORDEN_CATEGORIAS if c in tabla.index] +
                              [c for c in tabla.index if c not in ORDEN_CATEGORIAS],
                              columns=[s for s in ORDEN_SUCURSALES if s in tabla.columns] +
                              [s for s in tabla.columns if s not in ORDEN_SUCURSALES])
        imagen = eje.imshow(tabla.values, cmap=Estilo.mapa_color(), aspect="auto")
        eje.set_xticks(range(len(tabla.columns)), tabla.columns)
        eje.set_yticks(range(len(tabla.index)), tabla.index)
        eje.grid(False)
        for lado in ("left", "bottom"):
            eje.spines[lado].set_visible(False)
        maximo = tabla.values.max() or 1
        for fila in range(tabla.shape[0]):
            for col in range(tabla.shape[1]):
                valor = tabla.values[fila, col]
                intenso = valor / maximo > 0.55
                eje.text(col, fila, formateador(valor), ha="center", va="center", fontsize=Estilo.fs(9),
                         color=t["tinta_mapa"] if intenso else t["texto"])
        barra = lienzo.figura.colorbar(imagen, ax=eje, shrink=0.85)
        barra.ax.yaxis.set_major_formatter(FuncFormatter(formateador))
        barra.ax.tick_params(colors=t["texto2"], labelsize=Estilo.fs(8.5), length=0)
        barra.outline.set_visible(False)
        totales_fila = tabla.sum(axis=1)
        totales_col = tabla.sum(axis=0)

        def texto(f, c):
            valor = tabla.values[f, c]
            categoria, sucursal = tabla.index[f], tabla.columns[c]
            parte_sucursal = (f"{valor / totales_col.iloc[c] * 100:.1f}% de {texto_seguro(sucursal)}"
                              if totales_col.iloc[c] else "")
            parte_categoria = (f"{valor / totales_fila.iloc[f] * 100:.1f}% de {texto_seguro(categoria)}"
                               if totales_fila.iloc[f] else "")
            return tooltip(largo(valor), f"{categoria} · {sucursal}", parte_sucursal, parte_categoria,
                           "Clic para filtrar sucursal y categoría")

        lienzo.registrar_zona(ZonaMapa(eje, tabla.shape[0], tabla.shape[1], texto,
                                       lambda f, c: accion(tabla.columns[c], tabla.index[f])))
        LienzoInteractivo.titulo(eje, f"{metrica} por categoría y sucursal")
        lienzo.dibujar()

    @staticmethod
    def alertas(lienzo, datos, accion_sucursal, accion_categoria):
        t = Estilo.tema
        alertas = datos[datos["Estado_Stock"] != "Normal"]
        if alertas.empty:
            lienzo.sin_datos("No hay productos bajo el stock mínimo con estos filtros")
            return
        ejes = lienzo.reiniciar()
        for eje, columna, titulo, accion in (
            (ejes[0], "Sucursal", "Alertas de stock por sucursal", accion_sucursal),
            (ejes[1], "Categoria", "Alertas de stock por categoría", accion_categoria),
        ):
            tabla = pd.crosstab(alertas[columna], alertas["Estado_Stock"])
            for estado in ("Bajo mínimo", "Agotado"):
                if estado not in tabla.columns:
                    tabla[estado] = 0
            tabla = tabla.assign(total=tabla["Bajo mínimo"] + tabla["Agotado"]).sort_values("total")
            totales = datos.groupby(columna).size()
            bajo = eje.barh(tabla.index, tabla["Bajo mínimo"], color=t["bajo_minimo"], height=0.62,
                            edgecolor=t["superficie"], linewidth=1.5, label="Bajo mínimo")
            agotado = eje.barh(tabla.index, tabla["Agotado"], left=tabla["Bajo mínimo"], color=t["agotado"],
                               height=0.62, edgecolor=t["superficie"], linewidth=1.5, label="Agotado",
                               hatch="///" if Estilo.patrones else "")
            maximo = tabla["total"].max()
            for y, (nombre, fila) in enumerate(tabla.iterrows()):
                proporcion = fila["total"] / totales.get(nombre, fila["total"]) * 100
                eje.text(fila["total"] + maximo * 0.012, y, f"{int(fila['total'])} ({proporcion:.0f}%)",
                         va="center", fontsize=Estilo.fs(9), color=t["texto2"])
                detalle = tooltip(f"{int(fila['total'])} con alerta", nombre,
                                  f"{int(fila['Bajo mínimo'])} bajo mínimo · {int(fila['Agotado'])} agotados",
                                  f"{proporcion:.1f}% de sus registros", "Clic para ver estos productos en la tabla")
                for barra in (bajo[y], agotado[y]):
                    lienzo.registrar(barra, detalle, lambda n=nombre, a=accion: a(n))
            eje.set_xlim(0, maximo * 1.28)
            eje.grid(axis="y", visible=False)
            eje.xaxis.set_major_formatter(FuncFormatter(formato_miles))
            leyenda_suave(eje, loc="lower right")
            LienzoInteractivo.titulo(eje, titulo)
        lienzo.dibujar()

    @staticmethod
    def antiguedad(lienzo, datos, umbral):
        t = Estilo.tema
        (eje,) = lienzo.reiniciar()
        dias = datos["Dias_Sin_Ingreso"]
        limite = int(dias.max()) + 10
        conteos, bordes, barras = eje.hist(dias, bins=range(0, limite + 10, 10), color=t["serie"],
                                           edgecolor=t["superficie"], linewidth=1.5)
        for barra, inicio, fin, n in zip(barras, bordes[:-1], bordes[1:], conteos):
            if inicio >= umbral:
                barra.set_facecolor(t["bajo_minimo"])
                if Estilo.patrones:
                    barra.set_hatch("///")
            if n == 0:
                continue
            rango = datos[(dias >= inicio) & (dias < fin)]
            lienzo.registrar(barra, tooltip(f"{int(n)} registros", f"{int(inicio)} a {int(fin) - 1} días sin ingreso",
                                            f"Valor: ${rango['Valor_Inventario'].sum():,.2f}"))
        eje.axvline(umbral, color=t["texto"], linewidth=1.5, linestyle="--")
        lentos = datos[dias > umbral]
        eje.text(umbral + limite * 0.01, eje.get_ylim()[1] * 0.95,
                 f"Más de {umbral} días: {len(lentos)} registros\n"
                 f"Valor inmovilizado: ${lentos['Valor_Inventario'].sum():,.2f}",
                 fontsize=Estilo.fs(9.5), color=t["texto"], va="top")
        eje.set_xlabel("Días desde el último ingreso de mercadería", color=t["texto2"], fontsize=Estilo.fs(9.5))
        eje.set_ylabel("Registros", color=t["texto2"], fontsize=Estilo.fs(9.5))
        eje.grid(axis="x", visible=False)
        LienzoInteractivo.titulo(eje, "Antigüedad del último ingreso de inventario")
        lienzo.dibujar()

    @staticmethod
    def precios(lienzo, datos, logaritmica, seleccion, accion):
        t = Estilo.tema
        (eje,) = lienzo.reiniciar()
        orden = list(datos.groupby("Categoria")["Precio_Unitario"].median().sort_values().index)
        grupos = [datos.loc[datos["Categoria"] == c, "Precio_Unitario"] for c in orden]
        cajas = eje.boxplot(grupos, orientation="horizontal", patch_artist=True, widths=0.55,
                            medianprops={"color": t["texto"], "linewidth": 1.8},
                            whiskerprops={"color": t["texto2"]}, capprops={"color": t["texto2"]},
                            flierprops={"marker": "o", "markersize": 4, "markerfacecolor": t["texto2"],
                                        "markeredgecolor": t["texto2"], "alpha": 0.6})
        for caja, categoria, grupo in zip(cajas["boxes"], orden, grupos):
            caja.set_facecolor(Estilo.color_categoria(categoria) if seleccion in (None, categoria) else t["atenuado"])
            caja.set_edgecolor(t["superficie"])
            caja.set_linewidth(1)
            caja.set_hatch(Estilo.patron_categoria(categoria))
            q1, mediana, q3 = grupo.quantile([0.25, 0.5, 0.75])
            lienzo.registrar(caja, tooltip(
                f"Mediana ${mediana:,.2f}", categoria, f"Rango intercuartil: ${q1:,.2f} – ${q3:,.2f}",
                f"Mínimo ${grupo.min():,.2f} · Máximo ${grupo.max():,.2f}", f"{len(grupo)} registros",
                "Clic para filtrar esta categoría"), lambda c=categoria: accion(c))
        eje.set_yticks(range(1, len(orden) + 1), orden)
        if logaritmica:
            eje.set_xscale("log")
        eje.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}" if v >= 1 else f"${v:.2f}"))
        etiqueta = "Precio unitario (USD, escala logarítmica)" if logaritmica else "Precio unitario (USD)"
        eje.set_xlabel(etiqueta, color=t["texto2"], fontsize=Estilo.fs(9.5))
        eje.grid(axis="y", visible=False)
        LienzoInteractivo.titulo(eje, "Distribución de precios unitarios por categoría")
        lienzo.dibujar()

    @classmethod
    def top_productos(cls, lienzo, datos, metrica, cantidad, accion):
        t = Estilo.tema
        (eje,) = lienzo.reiniciar()
        agrupado = datos.groupby("ID_Producto").agg(
            Producto=("Producto", "first"), Categoria=("Categoria", "first"), Proveedor=("Proveedor", "first"),
            Valor=("Valor_Inventario", "sum"), Unidades=("Cantidad", "sum"), Sucursales=("Sucursal", "nunique"),
        )
        clave = "Valor" if metrica == "Valor del inventario" else "Unidades"
        top = agrupado.nlargest(cantidad, clave).iloc[::-1]
        etiquetas = [f"{p} ({i})" for i, p in zip(top.index, top["Producto"])]
        barras = eje.barh(etiquetas, top[clave], color=[Estilo.color_categoria(c) for c in top["Categoria"]],
                          height=0.66, edgecolor=t["superficie"], linewidth=0)
        formateador = formato_dolares if clave == "Valor" else formato_miles
        maximo = top[clave].max()
        cls.etiquetar_barras(eje, barras, top[clave], formateador, maximo)
        eje.set_xlim(0, maximo * 1.15)
        eje.grid(axis="y", visible=False)
        eje.tick_params(axis="y", labelsize=Estilo.fs(8.5 if cantidad > 15 else 9))
        eje.xaxis.set_major_formatter(FuncFormatter(formateador))
        for barra, (id_producto, fila) in zip(barras, top.iterrows()):
            barra.set_hatch(Estilo.patron_categoria(fila["Categoria"]))
            principal = f"${fila['Valor']:,.2f}" if clave == "Valor" else f"{int(fila['Unidades']):,} unidades"
            lienzo.registrar(barra, tooltip(
                principal, f"{fila['Producto']} ({id_producto})",
                f"{texto_seguro(fila['Categoria'])} · {texto_seguro(fila['Proveedor'])}",
                f"Presente en {fila['Sucursales']} sucursales", "Clic para ver el detalle"),
                lambda i=id_producto: accion(i))
        categorias = [c for c in ORDEN_CATEGORIAS if c in set(top["Categoria"])]
        manijas = [Patch(facecolor=Estilo.color_categoria(c), hatch=Estilo.patron_categoria(c),
                         edgecolor=t["superficie"], label=c) for c in categorias]
        leyenda_suave(eje, handles=manijas, loc="lower right")
        LienzoInteractivo.titulo(eje, f"Top {cantidad} productos por {metrica.lower()}")
        lienzo.dibujar()

    @staticmethod
    def detalle_producto(lienzo, filas):
        t = Estilo.tema
        (eje,) = lienzo.reiniciar()
        filas = filas.set_index("Sucursal").reindex(
            [s for s in ORDEN_SUCURSALES if s in set(filas["Sucursal"])])
        colores = [t["serie"] if e == "Normal" else t["agotado"] if e == "Agotado" else t["bajo_minimo"]
                   for e in filas["Estado_Stock"]]
        barras = eje.bar(filas.index, filas["Cantidad"], color=colores, width=0.6, edgecolor=t["superficie"])
        eje.scatter(range(len(filas)), filas["Stock_Minimo"], marker="_", s=900, linewidths=2.5,
                    color=t["texto"], zorder=5, label="Stock mínimo")
        for barra, (sucursal, fila) in zip(barras, filas.iterrows()):
            eje.text(barra.get_x() + barra.get_width() / 2, barra.get_height(), f"{fila['Cantidad']:,}",
                     ha="center", va="bottom", fontsize=Estilo.fs(9), color=t["texto2"])
            lienzo.registrar(barra, tooltip(
                f"{fila['Cantidad']:,} unidades", sucursal, f"Stock mínimo: {fila['Stock_Minimo']}",
                f"Estado: {fila['Estado_Stock']}", f"Valor: ${fila['Valor_Inventario']:,.2f}",
                f"Último ingreso: {fila['Fecha_Ultimo_Ingreso']:%Y-%m-%d}"))
        eje.grid(axis="x", visible=False)
        eje.set_ylim(0, max(filas["Cantidad"].max(), filas["Stock_Minimo"].max()) * 1.3 + 1)
        leyenda_suave(eje, loc="upper right", markerscale=0.35)
        LienzoInteractivo.titulo(eje, "Existencias por sucursal frente al stock mínimo")
        lienzo.dibujar()


class TarjetaIndicador(QFrame):
    pulsada = pyqtSignal()

    def __init__(self, titulo, pista, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(pista)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)
        self.etiqueta = QLabel(titulo)
        self.etiqueta.setObjectName("tituloTarjeta")
        self.valor = QLabel("—")
        self.valor.setObjectName("valorTarjeta")
        self.detalle = QLabel("")
        self.detalle.setObjectName("pistaTarjeta")
        layout.addWidget(self.etiqueta)
        layout.addWidget(self.valor)
        layout.addWidget(self.detalle)

    def establecer(self, texto, detalle="", alerta=False):
        self.valor.setText(texto)
        self.detalle.setText(detalle)
        self.valor.setStyleSheet(f"color: {Estilo.tema['alerta']};" if alerta else "")

    def mousePressEvent(self, evento):
        if evento.button() == Qt.LeftButton:
            self.pulsada.emit()
        super().mousePressEvent(evento)


class DialogoProducto(QDialog):
    def __init__(self, gestor, id_producto, parent=None):
        super().__init__(parent)
        filas = gestor.df[gestor.df["ID_Producto"] == id_producto]
        if filas.empty:
            raise InventarioError(f"No existe el producto {id_producto}.")
        base = filas.iloc[0]
        self.setWindowTitle(f"Detalle de {id_producto}")
        self.resize(820, 640)
        layout = QVBoxLayout(self)
        titulo = QLabel(f"{base['Producto']}  ·  {id_producto}")
        titulo.setObjectName("encabezado")
        subtitulo = QLabel(f"{base['Categoria']}  ·  Proveedor: {base['Proveedor']}  ·  "
                           f"Precio unitario: ${base['Precio_Unitario']:,.2f}  ·  "
                           f"Total: {filas['Cantidad'].sum():,} unidades (${filas['Valor_Inventario'].sum():,.2f})")
        subtitulo.setObjectName("subtitulo")
        subtitulo.setWordWrap(True)
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        self.lienzo = LienzoInteractivo(barra=False)
        self.lienzo.setMinimumHeight(300)
        GraficosInventario.detalle_producto(self.lienzo, filas)
        layout.addWidget(self.lienzo, stretch=1)

        mismo = gestor.df[gestor.df["Producto"] == base["Producto"]].groupby(["ID_Producto", "Proveedor"]).agg(
            Precio=("Precio_Unitario", "first"), Unidades=("Cantidad", "sum")).reset_index().sort_values("Precio")
        comparacion = QLabel("Mismo producto con otros proveedores (ordenado por precio):")
        comparacion.setObjectName("etiqueta")
        layout.addWidget(comparacion)
        tabla = QTableView()
        tabla.setModel(ModeloSimple(mismo.assign(Precio=mismo["Precio"].map(lambda v: f"${v:,.2f}")), tabla))
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabla.setMaximumHeight(190)
        layout.addWidget(tabla)

        botones = QDialogButtonBox()
        cerrar = botones.addButton("Cerrar", QDialogButtonBox.RejectRole)
        cerrar.setObjectName("primario")
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ajustes = QSettings("UGB", "VisorInventario")
        Estilo.activar(self.ajustes.value("tema", "oscuro"))
        Estilo.patrones = self.ajustes.value("patrones", False, type=bool)
        Estilo.tamano = self.ajustes.value("tamano", 10, type=int)
        self.gestor = GestorInventario()
        self.temporizador = QTimer(self)
        self.temporizador.setSingleShot(True)
        self.temporizador.setInterval(250)
        self.temporizador.timeout.connect(self.actualizar_vista)
        self.setWindowTitle("Visor de Inventario - Sucursales El Salvador")
        self.resize(1360, 880)
        geometria = self.ajustes.value("geometria")
        if geometria is not None:
            self.restoreGeometry(geometria)
        self.construir_menu()
        self.construir_interfaz()
        self.aplicar_estilo()
        self.statusBar().showMessage("Pase el cursor sobre los gráficos para ver detalles; haga clic para filtrar.")

    def construir_menu(self):
        archivo = self.menuBar().addMenu("&Archivo")
        self.agregar_accion(archivo, "&Abrir CSV...", "Ctrl+O", self.abrir_archivo)
        self.agregar_accion(archivo, "&Exportar datos filtrados...", "Ctrl+E", self.exportar_filtrado)
        self.agregar_accion(archivo, "Guardar &gráfico actual...", "Ctrl+S", self.exportar_grafico)
        archivo.addSeparator()
        self.agregar_accion(archivo, "&Salir", "Ctrl+Q", self.close)

        ver = self.menuBar().addMenu("&Ver")
        self.accion_oscuro = self.agregar_accion(ver, "Tema &oscuro", "Ctrl+T", self.cambiar_tema, True)
        self.accion_patrones = self.agregar_accion(
            ver, "&Patrones de relleno (daltonismo)", "Ctrl+P", self.cambiar_patrones, True)
        ver.addSeparator()
        self.agregar_accion(ver, "&Aumentar texto", QKeySequence.ZoomIn, lambda: self.cambiar_tamano(1))
        self.agregar_accion(ver, "&Reducir texto", QKeySequence.ZoomOut, lambda: self.cambiar_tamano(-1))
        self.agregar_accion(ver, "&Tamaño normal", "Ctrl+0", lambda: self.cambiar_tamano(0))
        ver.addSeparator()
        self.agregar_accion(ver, "&Limpiar filtros", "Esc", self.limpiar_filtros)

        ayuda = self.menuBar().addMenu("A&yuda")
        self.agregar_accion(ayuda, "&Cómo usar", "F1", self.mostrar_ayuda)
        self.agregar_accion(ayuda, "&Acerca de", None, self.mostrar_acerca_de)

    def agregar_accion(self, menu, texto, atajo, funcion, marcable=False):
        accion = QAction(texto, self)
        if atajo:
            accion.setShortcut(atajo)
        accion.setCheckable(marcable)
        accion.triggered.connect(funcion)
        menu.addAction(accion)
        return accion

    def construir_interfaz(self):
        central = QWidget()
        principal = QVBoxLayout(central)
        principal.setContentsMargins(16, 10, 16, 8)
        principal.setSpacing(10)

        cabecera = QHBoxLayout()
        textos = QVBoxLayout()
        encabezado = QLabel("Inventario consolidado por sucursal")
        encabezado.setObjectName("encabezado")
        self.subtitulo = QLabel("Cargue el archivo datos.csv para comenzar")
        self.subtitulo.setObjectName("subtitulo")
        textos.addWidget(encabezado)
        textos.addWidget(self.subtitulo)
        cabecera.addLayout(textos, stretch=1)
        self.boton_tema = QPushButton()
        self.boton_tema.setToolTip("Cambiar entre tema oscuro y claro (Ctrl+T)")
        self.boton_tema.clicked.connect(lambda: self.cambiar_tema(Estilo.nombre != "oscuro"))
        boton_abrir = QPushButton("Abrir CSV")
        boton_abrir.setObjectName("primario")
        boton_abrir.clicked.connect(self.abrir_archivo)
        cabecera.addWidget(self.boton_tema)
        cabecera.addWidget(boton_abrir)
        principal.addLayout(cabecera)

        filtros = QHBoxLayout()
        filtros.setSpacing(8)
        self.combos = {}
        for clave, titulo, ancho in (("Sucursal", "Sucursal", 150), ("Categoria", "Categoría", 165),
                                     ("Proveedor", "Proveedor", 195), ("Estado", "Estado", 120)):
            etiqueta = QLabel(titulo)
            etiqueta.setObjectName("etiqueta")
            combo = QComboBox()
            combo.setMinimumWidth(ancho)
            combo.currentIndexChanged.connect(self.actualizar_vista)
            self.combos[clave] = combo
            filtros.addWidget(etiqueta)
            filtros.addWidget(combo)
        self.combos["Estado"].blockSignals(True)
        self.combos["Estado"].addItems(ESTADOS)
        self.combos["Estado"].blockSignals(False)
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Buscar producto o código...")
        self.busqueda.setClearButtonEnabled(True)
        self.busqueda.setMinimumWidth(200)
        self.busqueda.textChanged.connect(lambda _: self.temporizador.start())
        boton_limpiar = QPushButton("Limpiar filtros")
        boton_limpiar.clicked.connect(self.limpiar_filtros)
        filtros.addWidget(self.busqueda, stretch=1)
        filtros.addWidget(boton_limpiar)
        principal.addLayout(filtros)

        tarjetas = QGridLayout()
        tarjetas.setSpacing(10)
        self.tarjetas = {
            "registros": TarjetaIndicador("Registros de inventario", "Clic: ver la tabla de datos"),
            "unidades": TarjetaIndicador("Unidades en existencia", "Clic: ver distribución por sucursal"),
            "valor": TarjetaIndicador("Valor del inventario", "Clic: ver composición por categoría"),
            "alertas": TarjetaIndicador("⚠ Alertas de stock", "Clic: mostrar solo productos con alerta"),
            "lentos": TarjetaIndicador("Sin ingreso reciente", "Clic: ver antigüedad del inventario"),
        }
        for columna, tarjeta in enumerate(self.tarjetas.values()):
            tarjetas.addWidget(tarjeta, 0, columna)
        principal.addLayout(tarjetas)

        self.pestanas = QTabWidget()
        self.lienzos = {}
        self.paginas = {}

        self.lienzos["sucursales"] = LienzoInteractivo(1, 2)
        self.agregar_pagina("sucursales", "Por sucursal", self.lienzos["sucursales"])
        self.lienzos["categorias"] = LienzoInteractivo(1, 2)
        self.agregar_pagina("categorias", "Por categoría", self.lienzos["categorias"])

        self.metrica_mapa = QComboBox()
        self.metrica_mapa.addItems(["Valor del inventario", "Unidades", "Registros", "Registros con alerta"])
        self.metrica_mapa.currentIndexChanged.connect(self.actualizar_vista)
        self.lienzos["mapa"] = LienzoInteractivo(1, 1)
        self.agregar_pagina("mapa", "Sucursal × categoría", self.lienzos["mapa"],
                            [QLabel("Métrica"), self.metrica_mapa])

        self.lienzos["alertas"] = LienzoInteractivo(1, 2)
        self.agregar_pagina("alertas", "Alertas de stock", self.lienzos["alertas"])

        self.umbral = QSpinBox()
        self.umbral.setRange(15, 240)
        self.umbral.setSingleStep(15)
        self.umbral.setValue(90)
        self.umbral.setSuffix(" días")
        self.umbral.valueChanged.connect(lambda _: self.temporizador.start())
        self.lienzos["antiguedad"] = LienzoInteractivo(1, 1)
        self.agregar_pagina("antiguedad", "Antigüedad", self.lienzos["antiguedad"],
                            [QLabel("Considerar sin movimiento después de"), self.umbral])

        self.escala_log = QCheckBox("Escala logarítmica")
        self.escala_log.setChecked(True)
        self.escala_log.toggled.connect(self.actualizar_vista)
        self.lienzos["precios"] = LienzoInteractivo(1, 1)
        self.agregar_pagina("precios", "Precios", self.lienzos["precios"], [self.escala_log])

        self.metrica_top = QComboBox()
        self.metrica_top.addItems(["Valor del inventario", "Unidades"])
        self.metrica_top.currentIndexChanged.connect(self.actualizar_vista)
        self.cantidad_top = QSpinBox()
        self.cantidad_top.setRange(5, 25)
        self.cantidad_top.setValue(10)
        self.cantidad_top.valueChanged.connect(lambda _: self.temporizador.start())
        self.lienzos["top"] = LienzoInteractivo(1, 1)
        self.agregar_pagina("top", "Top productos", self.lienzos["top"],
                            [QLabel("Ordenar por"), self.metrica_top, QLabel("Cantidad"), self.cantidad_top])

        self.modelo = ModeloTabla()
        self.tabla = QTableView()
        self.tabla.setModel(self.modelo)
        self.tabla.setSortingEnabled(True)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableView.SelectRows)
        self.tabla.setEditTriggers(QTableView.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.doubleClicked.connect(self.abrir_desde_tabla)
        self.agregar_pagina("datos", "Datos", self.tabla)

        self.texto_estadisticas = QPlainTextEdit()
        self.texto_estadisticas.setReadOnly(True)
        self.agregar_pagina("estadisticas", "Estadísticas", self.texto_estadisticas)
        self.pestanas.currentChanged.connect(lambda _: self.actualizar_barra_estado())

        principal.addWidget(self.pestanas, stretch=1)
        self.setCentralWidget(central)

        self.tarjetas["registros"].pulsada.connect(lambda: self.ir_a("datos"))
        self.tarjetas["unidades"].pulsada.connect(lambda: self.ir_a("sucursales"))
        self.tarjetas["valor"].pulsada.connect(lambda: self.ir_a("categorias"))
        self.tarjetas["alertas"].pulsada.connect(self.mostrar_alertas)
        self.tarjetas["lentos"].pulsada.connect(lambda: self.ir_a("antiguedad"))

    def agregar_pagina(self, clave, titulo, contenido, controles=None):
        pagina = QWidget()
        pagina.setObjectName("pagina")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(8, 8, 8, 4)
        if controles:
            fila = QHBoxLayout()
            for control in controles:
                if isinstance(control, QLabel):
                    control.setObjectName("etiqueta")
                fila.addWidget(control)
            fila.addStretch()
            layout.addLayout(fila)
        layout.addWidget(contenido, stretch=1)
        self.paginas[clave] = self.pestanas.addTab(pagina, titulo)

    def aplicar_estilo(self):
        QApplication.instance().setStyleSheet(Estilo.hoja_qt())
        fuente = QFont("Consolas")
        fuente.setStyleHint(QFont.Monospace)
        fuente.setPointSize(max(Estilo.tamano - 1, 7))
        self.texto_estadisticas.setFont(fuente)
        self.boton_tema.setText("☀ Tema claro" if Estilo.nombre == "oscuro" else "☾ Tema oscuro")
        self.accion_oscuro.setChecked(Estilo.nombre == "oscuro")
        self.accion_patrones.setChecked(Estilo.patrones)
        self.actualizar_vista()

    def cambiar_tema(self, oscuro):
        Estilo.activar("oscuro" if oscuro else "claro")
        self.ajustes.setValue("tema", Estilo.nombre)
        self.aplicar_estilo()

    def cambiar_patrones(self, activo):
        Estilo.patrones = bool(activo)
        self.ajustes.setValue("patrones", Estilo.patrones)
        self.aplicar_estilo()

    def cambiar_tamano(self, paso):
        Estilo.tamano = 10 if paso == 0 else min(max(Estilo.tamano + paso, 8), 16)
        self.ajustes.setValue("tamano", Estilo.tamano)
        self.aplicar_estilo()

    def ir_a(self, clave):
        self.pestanas.setCurrentIndex(self.paginas[clave])

    def cargar_datos(self, ruta):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.gestor.cargar(ruta)
        except InventarioError as error:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "No se pudo cargar el inventario", str(error))
            return False
        except Exception as error:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error inesperado", f"{type(error).__name__}: {error}")
            return False
        QApplication.restoreOverrideCursor()
        self.poblar_filtros()
        self.subtitulo.setText(
            f"Fuente: {self.gestor.ruta.name}  ·  {len(self.gestor.df):,} registros  ·  "
            f"{self.gestor.df['ID_Producto'].nunique()} productos  ·  "
            f"corte al {self.gestor.fecha_corte:%d/%m/%Y}")
        self.actualizar_vista()
        return True

    def poblar_filtros(self):
        for clave in ("Sucursal", "Categoria", "Proveedor"):
            combo = self.combos[clave]
            combo.blockSignals(True)
            combo.clear()
            combo.addItems([TODAS] + self.gestor.valores(clave))
            combo.blockSignals(False)

    def filtros(self):
        valores = {clave: combo.currentText() or (TODAS if clave != "Estado" else "Todos")
                   for clave, combo in self.combos.items()}
        valores["Texto"] = self.busqueda.text()
        return valores

    def establecer_filtros(self, **cambios):
        for clave, valor in cambios.items():
            combo = self.combos[clave]
            combo.blockSignals(True)
            indice = combo.findText(valor)
            combo.setCurrentIndex(indice if indice >= 0 else 0)
            combo.blockSignals(False)
        self.actualizar_vista()

    def alternar_filtro(self, clave, valor):
        actual = self.combos[clave].currentText()
        self.establecer_filtros(**{clave: TODAS if actual == valor else valor})

    def filtrar_celda(self, sucursal, categoria):
        actual = (self.combos["Sucursal"].currentText(), self.combos["Categoria"].currentText())
        if actual == (sucursal, categoria):
            self.establecer_filtros(Sucursal=TODAS, Categoria=TODAS)
        else:
            self.establecer_filtros(Sucursal=sucursal, Categoria=categoria)

    def mostrar_alertas(self):
        self.establecer_filtros(Estado="Con alerta")
        self.ir_a("alertas")

    def alerta_por(self, clave, valor):
        self.establecer_filtros(**{clave: valor, "Estado": "Con alerta"})
        self.ir_a("datos")

    def limpiar_filtros(self):
        for combo in self.combos.values():
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self.busqueda.blockSignals(True)
        self.busqueda.clear()
        self.busqueda.blockSignals(False)
        self.actualizar_vista()

    def actualizar_vista(self):
        if not self.gestor.cargado:
            return
        filtros = self.filtros()
        datos = self.gestor.filtrar(filtros)
        self.actualizar_tarjetas(datos)
        self.modelo.actualizar(datos)
        self.actualizar_barra_estado(len(datos))
        if datos.empty:
            for lienzo in self.lienzos.values():
                lienzo.sin_datos()
            self.texto_estadisticas.setPlainText("Sin datos para los filtros seleccionados.")
            return
        seleccion = {c: (None if filtros[c] == TODAS else filtros[c]) for c in ("Sucursal", "Categoria")}
        contexto_sucursal = self.gestor.filtrar(filtros, excluir=("Sucursal",))
        contexto_categoria = self.gestor.filtrar(filtros, excluir=("Categoria",))
        tareas = {
            "sucursales": lambda l: GraficosInventario.sucursales(
                l, contexto_sucursal, seleccion["Sucursal"], lambda v: self.alternar_filtro("Sucursal", v)),
            "categorias": lambda l: GraficosInventario.categorias(
                l, contexto_categoria, seleccion["Categoria"], lambda v: self.alternar_filtro("Categoria", v)),
            "mapa": lambda l: GraficosInventario.mapa_calor(
                l, datos, self.metrica_mapa.currentText(), self.filtrar_celda),
            "alertas": lambda l: GraficosInventario.alertas(
                l, datos, lambda v: self.alerta_por("Sucursal", v), lambda v: self.alerta_por("Categoria", v)),
            "antiguedad": lambda l: GraficosInventario.antiguedad(l, datos, self.umbral.value()),
            "precios": lambda l: GraficosInventario.precios(
                l, contexto_categoria, self.escala_log.isChecked(), seleccion["Categoria"],
                lambda v: self.alternar_filtro("Categoria", v)),
            "top": lambda l: GraficosInventario.top_productos(
                l, datos, self.metrica_top.currentText(), self.cantidad_top.value(), self.abrir_producto),
        }
        for clave, tarea in tareas.items():
            try:
                tarea(self.lienzos[clave])
            except Exception as error:
                self.lienzos[clave].sin_datos(f"No se pudo dibujar este gráfico: {error}")
        self.texto_estadisticas.setPlainText(GestorInventario.resumen_estadistico(datos))

    def actualizar_tarjetas(self, datos):
        umbral = self.umbral.value()
        i = GestorInventario.indicadores(datos, umbral)
        self.tarjetas["registros"].establecer(f"{i['registros']:,}", f"{i['productos']} productos distintos")
        self.tarjetas["unidades"].establecer(f"{i['unidades']:,}", "unidades disponibles")
        self.tarjetas["valor"].establecer(formato_dolares(i["valor"]), f"${i['valor']:,.2f}")
        porcentaje = i["alertas"] / i["registros"] * 100 if i["registros"] else 0
        self.tarjetas["alertas"].establecer(f"{i['alertas']:,}", f"{porcentaje:.1f}% · {i['agotados']} agotados",
                                            alerta=i["alertas"] > 0)
        self.tarjetas["lentos"].etiqueta.setText(f"Sin ingreso > {umbral} días")
        self.tarjetas["lentos"].establecer(f"{i['lentos']:,}", f"${i['valor_lento']:,.2f} inmovilizados")

    def actualizar_barra_estado(self, cantidad=None):
        if not self.gestor.cargado:
            return
        f = self.filtros()
        activos = [f"{c} = {v}" for c, v in f.items() if c != "Texto" and v not in (TODAS, "Todos")]
        if f["Texto"].strip():
            activos.append(f"búsqueda = \"{f['Texto'].strip()}\"")
        cantidad = cantidad if cantidad is not None else self.modelo.rowCount()
        resumen = " · ".join(activos) if activos else "sin filtros"
        if self.pestanas.currentIndex() == self.paginas["datos"]:
            pista = "Doble clic en una fila para ver el detalle"
        else:
            pista = "Pase el cursor para ver detalles · clic para filtrar · Esc limpia los filtros"
        self.statusBar().showMessage(f"{cantidad:,} registros ({resumen})   |   {pista}")

    def abrir_producto(self, id_producto):
        try:
            DialogoProducto(self.gestor, id_producto, self).exec_()
        except InventarioError as error:
            QMessageBox.warning(self, "Producto", str(error))

    def abrir_desde_tabla(self, indice):
        self.abrir_producto(self.modelo.fila(indice.row())["ID_Producto"])

    def abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar inventario", str(RUTA_DATOS.parent), "Archivos CSV (*.csv)")
        if ruta:
            self.cargar_datos(ruta)

    def exportar_filtrado(self):
        if not self.gestor.cargado:
            QMessageBox.information(self, "Exportar", "Primero cargue un inventario.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar datos filtrados", str(RUTA_DATOS.parent / "inventario_filtrado.csv"),
            "Archivos CSV (*.csv)")
        if not ruta:
            return
        try:
            datos = self.gestor.filtrar(self.filtros())
            datos[GestorInventario.COLUMNAS_REQUERIDAS + ["Valor_Inventario", "Estado_Stock"]].to_csv(
                ruta, index=False, encoding="utf-8")
            self.statusBar().showMessage(f"{len(datos)} registros exportados a {ruta}", 6000)
        except PermissionError:
            QMessageBox.warning(self, "Exportar", "El archivo está abierto en otro programa.")
        except OSError as error:
            QMessageBox.critical(self, "Exportar", f"No se pudo guardar el archivo:\n{error}")

    def exportar_grafico(self):
        actual = self.pestanas.currentIndex()
        clave = next((c for c, i in self.paginas.items() if i == actual and c in self.lienzos), None)
        if clave is None:
            QMessageBox.information(self, "Guardar gráfico", "Seleccione una pestaña que contenga un gráfico.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar gráfico", str(RUTA_DATOS.parent / f"grafico_{clave}.png"),
            "Imagen PNG (*.png);;Documento PDF (*.pdf);;Vectorial SVG (*.svg)")
        if not ruta:
            return
        try:
            self.lienzos[clave].figura.savefig(ruta, dpi=200, facecolor=Estilo.tema["superficie"])
            self.statusBar().showMessage(f"Gráfico guardado en {ruta}", 6000)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Guardar gráfico", f"No se pudo guardar:\n{error}")

    def mostrar_ayuda(self):
        QMessageBox.information(
            self, "Cómo usar",
            "• Pase el cursor sobre barras, porciones o celdas para ver sus valores.\n"
            "• Haga clic en una barra, porción o celda para filtrar; clic de nuevo para quitar el filtro.\n"
            "• Las tarjetas superiores también se pueden pulsar.\n"
            "• En Datos, doble clic en una fila abre el detalle del producto.\n"
            "• En Top productos, clic en una barra abre el detalle.\n\n"
            "Atajos: Ctrl+T tema · Ctrl+P patrones · Ctrl+ y Ctrl- tamaño del texto · "
            "Esc limpiar filtros · Ctrl+S guardar gráfico · Ctrl+E exportar CSV",
        )

    def mostrar_acerca_de(self):
        QMessageBox.about(
            self, "Acerca de",
            "<b>Visor de Inventario</b><br>Programación Computacional III<br>"
            "Universidad Gerardo Barrios<br><br>Python · Pandas · PyQt5 · Matplotlib",
        )

    def closeEvent(self, evento):
        self.ajustes.setValue("geometria", self.saveGeometry())
        super().closeEvent(evento)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ventana = VentanaPrincipal()
    ventana.show()
    if RUTA_DATOS.exists():
        ventana.cargar_datos(RUTA_DATOS)
    else:
        QMessageBox.information(
            ventana, "Inventario no encontrado",
            "No se encontró datos.csv junto al programa.\n"
            "Ejecute primero generar_datos.py o abra un archivo CSV desde el menú Archivo.",
        )
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
