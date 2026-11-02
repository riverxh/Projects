# Criterio de relevancia de búsquedas

Se revisó el pool de 110 pares consulta-fragmento: unión de los cinco primeros resultados de BM25 y kNN para 14 consultas. Durante la anotación el pool se ordenó por identificador, sin método, posición ni score. Los juicios se conservan en `config/relevancia.json`, con una justificación para cada par.

| Grado | Interpretación |
|---|---|
| 2 | El pasaje responde directamente a la pregunta, respetando su ubicación y periodo cuando son específicos. |
| 1 | Aporta contexto o una parte de la explicación, pero falta una relación, precisión o resultado pedido. |
| 0 | No responde, trata otra ubicación/periodo específico o no contiene evidencia para el tema solicitado. |

La precisión@5 estricta cuenta únicamente grado 2. La contextual cuenta grados 1 y 2. El recíproco del primer relevante usa solo grado 2 y vale cero cuando no aparece ninguno. Un resultado de otro territorio no se convierte en pertinente solo por tratar la misma amenaza natural. Los documentos históricos no se usan para afirmar vigencia jurídica actual.

Q01–Q04 son consultas de desarrollo, ya utilizadas en el anteproyecto o piloto. Q05–Q12 se reservaron para la comparación interna y no se modificaron los parámetros de búsqueda después de consultarlas. Q13–Q14 son controles fuera de tema/cobertura, informados por separado.

Estos son juicios documentales internos, no una validación independiente por dos evaluadores. El estudiante debe revisar las justificaciones y ejemplos antes de presentar; no se midió acuerdo entre anotadores. No se pretende exhaustividad: el pool top5 permite precisión y primer relevante, pero no recall global. El solapamiento puede producir pasajes cercanos de una misma página; las métricas evalúan fragmentos, no documentos únicos.

No se afinó un umbral de respuesta con los dos controles. Ambos buscadores siempre generan un ranking: un score alto no acredita que exista respuesta. Tampoco se comparan numéricamente los scores BM25 y los de kNN entre sí.
