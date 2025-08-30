# utils.py - Funciones de utilidad para la aplicación
import os
import pandas as pd
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FileProcessor:
    """Clase para procesar diferentes tipos de archivos"""
    
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Verificar si el archivo tiene una extensión permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileProcessor.ALLOWED_EXTENSIONS
    
    @staticmethod
    def secure_save_filename(filename: str) -> str:
        """Generar nombre seguro para el archivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        secure_name = secure_filename(filename)
        return f"{timestamp}_{secure_name}"
    
    @staticmethod
    def read_excel_file(filepath: str) -> pd.DataFrame:
        """Leer archivo Excel con manejo robusto de errores"""
        try:
            # Intentar con openpyxl primero (archivos modernos)
            df = pd.read_excel(filepath, engine='openpyxl')
            logger.info(f"Archivo leído con openpyxl: {filepath}")
            return df
        except Exception as e1:
            try:
                # Intentar con xlrd para archivos legacy
                df = pd.read_excel(filepath, engine='xlrd')
                logger.info(f"Archivo leído con xlrd: {filepath}")
                return df
            except Exception as e2:
                logger.error(f"Error leyendo archivo con ambos engines: openpyxl={e1}, xlrd={e2}")
                raise Exception(f"No se pudo leer el archivo Excel: {e2}")
    
    @staticmethod
    def read_csv_file(filepath: str) -> pd.DataFrame:
        """Leer archivo CSV con detección automática de formato"""
        try:
            # Detectar separador y encoding
            with open(filepath, 'rb') as f:
                raw_data = f.read(10000)  # Leer primeros 10KB
                
            # Detectar encoding
            encoding = 'utf-8'
            for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    raw_data.decode(enc)
                    encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
            
            # Detectar separador
            sample_text = raw_data.decode(encoding, errors='ignore')
            separators = [',', ';', '\t', '|']
            separator = ','
            max_columns = 0
            
            for sep in separators:
                lines = sample_text.split('\n')[:5]  # Primeras 5 líneas
                columns = max([len(line.split(sep)) for line in lines if line.strip()])
                if columns > max_columns:
                    max_columns = columns
                    separator = sep
            
            # Leer CSV con parámetros detectados
            df = pd.read_csv(filepath, encoding=encoding, sep=separator)
            logger.info(f"CSV leído: {filepath}, encoding={encoding}, separator={separator}")
            return df
            
        except Exception as e:
            logger.error(f"Error leyendo archivo CSV: {e}")
            raise Exception(f"No se pudo leer el archivo CSV: {e}")
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Limpiar y preparar DataFrame"""
        # Remover filas completamente vacías
        df = df.dropna(how='all')
        
        # Llenar valores NaN con string vacío
        df = df.fillna('')
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Convertir todas las columnas a string para búsqueda
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        
        return df

class SearchEngine:
    """Motor de búsqueda avanzado"""
    
    @staticmethod
    def simple_search(query: str, data: List[Dict], case_sensitive: bool = False) -> List[Dict]:
        """Búsqueda simple por texto"""
        if not case_sensitive:
            query = query.lower()
        
        results = []
        for item in data:
            found = False
            match_fields = []
            
            for key, value in item.items():
                value_str = str(value)
                if not case_sensitive:
                    value_str = value_str.lower()
                
                if query in value_str:
                    found = True
                    match_fields.append(key)
            
            if found:
                result = item.copy()
                result['_match_fields'] = match_fields
                result['_relevance'] = SearchEngine.calculate_relevance(query, item)
                results.append(result)
        
        return sorted(results, key=lambda x: x.get('_relevance', 0), reverse=True)
    
    @staticmethod
    def exact_search(query: str, data: List[Dict], case_sensitive: bool = False) -> List[Dict]:
        """Búsqueda exacta"""
        if not case_sensitive:
            query = query.lower()
        
        results = []
        for item in data:
            for key, value in item.items():
                value_str = str(value)
                if not case_sensitive:
                    value_str = value_str.lower()
                
                if query == value_str:
                    result = item.copy()
                    result['_match_fields'] = [key]
                    result['_relevance'] = 100  # Máxima relevancia para coincidencias exactas
                    results.append(result)
                    break
        
        return results
    
    @staticmethod
    def field_search(field: str, query: str, data: List[Dict], case_sensitive: bool = False) -> List[Dict]:
        """Búsqueda en un campo específico"""
        if not case_sensitive:
            query = query.lower()
        
        results = []
        for item in data:
            if field in item:
                value_str = str(item[field])
                if not case_sensitive:
                    value_str = value_str.lower()
                
                if query in value_str:
                    result = item.copy()
                    result['_match_fields'] = [field]
                    result['_relevance'] = SearchEngine.calculate_field_relevance(query, value_str)
                    results.append(result)
        
        return sorted(results, key=lambda x: x.get('_relevance', 0), reverse=True)
    
    @staticmethod
    def advanced_search(query: str, data: List[Dict]) -> List[Dict]:
        """Búsqueda avanzada con operadores"""
        try:
            # Procesar consulta avanzada: "campo:valor AND otro_campo:otro_valor"
            query = query.replace(' AND ', ' and ').replace(' OR ', ' or ')
            query = query.replace(' NOT ', ' not ')
            
            results = []
            for item in data:
                if SearchEngine.evaluate_advanced_query(query, item):
                    result = item.copy()
                    result['_relevance'] = SearchEngine.calculate_advanced_relevance(query, item)
                    results.append(result)
            
            return sorted(results, key=lambda x: x.get('_relevance', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Error en búsqueda avanzada: {e}")
            # Fallback a búsqueda simple
            return SearchEngine.simple_search(query, data)
    
    @staticmethod
    def calculate_relevance(query: str, item: Dict) -> float:
        """Calcular relevancia de un resultado"""
        relevance = 0.0
        query_words = query.lower().split()
        
        for key, value in item.items():
            if key.startswith('_'):  # Ignorar campos especiales
                continue
                
            value_str = str(value).lower()
            
            for word in query_words:
                if word in value_str:
                    # Coincidencia exacta del campo completo
                    if word == value_str:
                        relevance += 20.0
                    # Palabra al inicio del campo
                    elif value_str.startswith(word):
                        relevance += 10.0
                    # Palabra al final del campo
                    elif value_str.endswith(word):
                        relevance += 5.0
                    # Palabra en cualquier parte
                    else:
                        relevance += 2.0
                    
                    # Bonus por longitud de coincidencia
                    relevance += len(word) * 0.1
        
        return relevance
    
    @staticmethod
    def calculate_field_relevance(query: str, field_value: str) -> float:
        """Calcular relevancia para búsqueda en campo específico"""
        query_lower = query.lower()
        field_lower = field_value.lower()
        
        if query_lower == field_lower:
            return 100.0
        elif field_lower.startswith(query_lower):
            return 80.0
        elif field_lower.endswith(query_lower):
            return 60.0
        elif query_lower in field_lower:
            # Calcular posición relativa
            position = field_lower.find(query_lower)
            position_score = (len(field_lower) - position) / len(field_lower)
            return 40.0 + (position_score * 20.0)
        
        return 0.0
    
    @staticmethod
    def calculate_advanced_relevance(query: str, item: Dict) -> float:
        """Calcular relevancia para búsqueda avanzada"""
        # Implementación simplificada
        relevance = 0.0
        terms = re.findall(r'(\w+):(\w+)', query)
        
        for field, value in terms:
            if field in item:
                item_value = str(item[field]).lower()
                if value.lower() in item_value:
                    relevance += 50.0
        
        return relevance
    
    @staticmethod
    def evaluate_advanced_query(query: str, item: Dict) -> bool:
        """Evaluar consulta avanzada con operadores booleanos"""
        try:
            # Extraer términos campo:valor
            field_terms = re.findall(r'(\w+):(\w+)', query)
            conditions = []
            
            query_copy = query
            for field, value in field_terms:
                condition_result = False
                if field in item:
                    item_value = str(item[field]).lower()
                    condition_result = value.lower() in item_value
                
                # Reemplazar en la consulta
                pattern = f"{field}:{value}"
                query_copy = query_copy.replace(pattern, str(condition_result))
            
            # Evaluar expresión booleana
            # Seguridad: solo permitir True, False, and, or, not, paréntesis
            allowed_tokens = {'True', 'False', 'and', 'or', 'not', '(', ')', ' '}
            if all(token in allowed_tokens or token.isspace() for token in query_copy):
                return eval(query_copy)
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluando consulta avanzada: {e}")
            return False

class DataAnalyzer:
    """Analizador de datos para estadísticas"""
    
    @staticmethod
    def get_basic_stats(data: List[Dict]) -> Dict[str, Any]:
        """Obtener estadísticas básicas de los datos"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        stats = {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'data_types': {},
            'null_counts': {},
            'unique_counts': {},
            'sample_data': data[:3] if len(data) > 3 else data
        }
        
        for col in df.columns:
            if col.startswith('_'):  # Ignorar campos especiales
                continue
                
            stats['data_types'][col] = str(df[col].dtype)
            stats['null_counts'][col] = int(df[col].isnull().sum())
            stats['unique_counts'][col] = int(df[col].nunique())
        
        return stats
    
    @staticmethod
    def get_search_analytics(search_history: List[Dict]) -> Dict[str, Any]:
        """Analizar historial de búsquedas"""
        if not search_history:
            return {}
        
        df = pd.DataFrame(search_history)
        
        analytics = {
            'total_searches': len(search_history),
            'unique_queries': df['query'].nunique(),
            'most_common_queries': df['query'].value_counts().head(10).to_dict(),
            'searches_by_type': df.get('type', pd.Series(['general'] * len(df))).value_counts().to_dict(),
            'recent_searches': search_history[-10:] if len(search_history) > 10 else search_history
        }
        
        # Análisis temporal si hay timestamps
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            analytics['searches_by_hour'] = df['hour'].value_counts().sort_index().to_dict()
        
        return analytics

class ExportManager:
    """Manejador de exportaciones"""
    
    @staticmethod
    def to_csv(data: List[Dict], filename: str = None) -> str:
        """Exportar datos a CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.csv"
        
        # Limpiar datos de campos especiales
        clean_data = []
        for item in data:
            clean_item = {k: v for k, v in item.items() if not k.startswith('_')}
            clean_data.append(clean_item)
        
        df = pd.DataFrame(clean_data)
        filepath = os.path.join('exports', filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        return filepath
    
    @staticmethod
    def to_excel(data: List[Dict], filename: str = None, sheet_name: str = 'Datos') -> str:
        """Exportar datos a Excel"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.xlsx"
        
        # Limpiar datos de campos especiales
        clean_data = []
        for item in data:
            clean_item = {k: v for k, v in item.items() if not k.startswith('_')}
            clean_data.append(clean_item)
        
        df = pd.DataFrame(clean_data)
        filepath = os.path.join('exports', filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return filepath
    
    @staticmethod
    def to_json(data: List[Dict], filename: str = None) -> str:
        """Exportar datos a JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.json"
        
        # Limpiar datos de campos especiales
        clean_data = []
        for item in data:
            clean_item = {k: v for k, v in item.items() if not k.startswith('_')}
            clean_data.append(clean_item)
        
        filepath = os.path.join('exports', filename)
        
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
        
        return filepath

class ValidationUtils:
    """Utilidades de validación"""
    
    @staticmethod
    def validate_search_query(query: str) -> Tuple[bool, str]:
        """Validar consulta de búsqueda"""
        if not query or not query.strip():
            return False, "La consulta no puede estar vacía"
        
        if len(query) > 1000:
            return False, "La consulta es demasiado larga (máximo 1000 caracteres)"
        
        # Verificar caracteres peligrosos para evaluación
        dangerous_chars = ['__', 'eval', 'exec', 'import', 'open', 'file']
        query_lower = query.lower()
        
        for char in dangerous_chars:
            if char in query_lower:
                return False, f"Carácter o palabra no permitida: {char}"
        
        return True, "Consulta válida"
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> Tuple[bool, str]:
        """Validar tamaño de archivo"""
        if file_size > max_size:
            max_mb = max_size // (1024 * 1024)
            return False, f"El archivo es demasiado grande (máximo {max_mb}MB)"
        
        return True, "Tamaño válido"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizar nombre de archivo"""
        # Remover caracteres peligrosos
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limitar longitud
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename