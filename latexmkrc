# ---------------------------------------------------------------
# latexmkrc — salvaguarda contra el bloqueo de main.pdf en Windows
# ---------------------------------------------------------------
# Si un visor de PDF (por ejemplo una pestaña de vista previa de VS Code)
# mantiene main.pdf abierto, pdfTeX no puede reemplazarlo y aborta con:
#
#   ! I can't write on file `main.pdf'.
#   Emergency stop.
#
# Renombrar sí es posible aunque el archivo esté bloqueado, así que
# apartamos el PDF anterior justo antes de cada pasada de pdflatex.
# Los archivos apartados se borran al terminar, salvo que el visor
# todavía los retenga (en ese caso se limpian en la compilación siguiente).

our $pdf_apartado;

sub apartar_pdf {
	my $pdf = 'main.pdf';
	return unless -e $pdf;

	my $n = 0;
	my $dest;
	do {
		$dest = $n ? "main.pdf.viejo.$n" : 'main.pdf.viejo';
		$n++;
	} while (-e $dest and not unlink $dest);

	$pdf_apartado = $dest if rename $pdf, $dest;
}

$pdflatex = 'internal pdflatex_sin_bloqueo %O %S';

sub pdflatex_sin_bloqueo {
	apartar_pdf();
	return system 'pdflatex', @_;
}

END {
	if ($pdf_apartado and not -e 'main.pdf') {
		# La compilación no produjo un PDF nuevo: devolvemos el anterior.
		rename $pdf_apartado, 'main.pdf';
	} else {
		unlink $_ for grep { -f $_ } glob('main.pdf.viejo*');
	}
}
