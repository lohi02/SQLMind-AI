from typing import List, Any, Optional, Dict
import plotly.express as px
import plotly.graph_objects as go

class ChartGenerator:
    @staticmethod
    def create_chart(columns: List[str], rows: List[List[Any]]) -> Optional[go.Figure]:
        """
        Analyzes query result headers and row types to automatically generate an appropriate Plotly chart.
        Returns a Plotly Figure or None if the dataset is not suitable for graphing.
        """
        if not columns or not rows or len(rows) == 0 or len(columns) < 2:
            return None

        # Determine column data types from first non-null sample row
        col_types = []
        sample_row = rows[0]
        
        for idx, val in enumerate(sample_row):
            if isinstance(val, (int, float)):
                col_types.append("numeric")
            elif isinstance(val, str):
                # Simple check for date patterns
                val_clean = val.strip()
                if len(val_clean) == 10 and val_clean[4] == '-' and val_clean[7] == '-':
                    col_types.append("date")
                else:
                    col_types.append("string")
            else:
                col_types.append("other")

        # Find categorical, date, and numerical column indices
        numeric_indices = [i for i, t in enumerate(col_types) if t == "numeric"]
        string_indices = [i for i, t in enumerate(col_types) if t == "string"]
        date_indices = [i for i, t in enumerate(col_types) if t == "date"]

        if not numeric_indices:
            return None

        y_col_idx = numeric_indices[0]
        y_label = columns[y_col_idx]

        # Scenario 1: Date column + Numeric column -> Line Chart
        if date_indices:
            x_col_idx = date_indices[0]
            x_label = columns[x_col_idx]
            x_data = [row[x_col_idx] for row in rows]
            y_data = [row[y_col_idx] for row in rows]
            
            fig = px.line(
                x=x_data,
                y=y_data,
                labels={'x': x_label, 'y': y_label},
                title=f"{y_label} over {x_label}",
                markers=True
            )
            fig.update_layout(template="plotly_dark")
            return fig

        # Scenario 2: String column + Numeric column -> Bar Chart
        if string_indices:
            x_col_idx = string_indices[0]
            x_label = columns[x_col_idx]
            x_data = [str(row[x_col_idx]) for row in rows]
            y_data = [row[y_col_idx] for row in rows]

            fig = px.bar(
                x=x_data,
                y=y_data,
                labels={'x': x_label, 'y': y_label},
                title=f"{y_label} by {x_label}",
                color=y_data,
                color_continuous_scale="Viridis"
            )
            fig.update_layout(template="plotly_dark", coloraxis_showscale=False)
            return fig

        # Scenario 3: Multiple Numeric columns -> Bar comparison
        if len(numeric_indices) >= 2:
            x_col_idx = numeric_indices[0]
            y_col_idx = numeric_indices[1]
            x_label = columns[x_col_idx]
            y_label = columns[y_col_idx]
            
            fig = px.scatter(
                x=[row[x_col_idx] for row in rows],
                y=[row[y_col_idx] for row in rows],
                labels={'x': x_label, 'y': y_label},
                title=f"{y_label} vs {x_label}"
            )
            fig.update_layout(template="plotly_dark")
            return fig

        return None
