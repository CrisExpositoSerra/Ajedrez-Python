#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random, pygame, sys, os
from pygame.locals import *
from copy import deepcopy

############################################### Clase Main ################################################
#                       Maneja los eventos del mouse y el loop principal del juego                        #
###########################################################################################################
class Main:	
	
	LARGO_VENTANA = None
	ANCHO_VENTANA = None
	
	jugador = None
	tablero = None
	calculos = None
	grafico = None
	logico = None
	
	# velocidad promedio de cuadros por segundo
	FPS = 114
	
	FPSCLOCK = None
	SUPERFICIE = None
	
	def __init__(self, config):
		self.LARGO_VENTANA = config["LARGO_VENTANA"]
		self.ANCHO_VENTANA = config["ANCHO_VENTANA"]
		
		# iniciar el modulo pygame, el objeto FPS y la ventana
		pygame.init()
		self.FPSCLOCK = pygame.time.Clock()
		#self.SUPERFICIE = pygame.display.set_mode((self.LARGO_VENTANA, self.ANCHO_VENTANA))
		#pygame.display.set_caption('Ajedrez Vikingo')
		
		# instancia de clases 
		self.jugador = Jugador()
		self.tablero = Tablero(self.jugador, config)
		self.calculos = Calculos(config)
		self.logico = Logico(self.jugador, self.tablero, self.calculos, config)
		self.grafico = Grafico(self.logico, self.SUPERFICIE, config)
		
	
	def iniciar(self):
	
		# almacenan las coordenadas del mouse
		mousex = 0 
		mousey = 0 
		
		# boolean para saber si hay alguna ficha seleccionada
		seleccion = False
		
		jaque = False
		peligro = False
		
		# sirve para almacenar la posicion de la ficha seleccionada por el clic
		fichaSeleccion = ""
		
		while True: # loop principal del juego
		
			mouseClic = False
			
			self.grafico.dibujarVentana()
			if jaque:
				self.grafico.dibujarAlerta(self.calculos.getEsquinas(), "verde")
			if peligro:
				self.grafico.dibujarAlerta(self.calculos.getPeligroRey(), "roja")
			if seleccion:
				self.grafico.dibujarCaminoIluminado(None, None)
				
			
			for evento in pygame.event.get():
				if evento.type == QUIT or (evento.type == KEYUP and evento.key == K_ESCAPE):
					pygame.quit()
					sys.exit()
				elif not mouseClic and evento.type == MOUSEMOTION:
					mousex, mousey = evento.pos 
				elif not mouseClic and evento.type == MOUSEBUTTONUP:
					mousex, mousey = evento.pos
					mouseClic = True	
					
			# comprobar si el mouse esta actualmente en un cuadro
			cuadrox, cuadroy = self.grafico.getCuadroEnPixel(mousex, mousey)					
			
			if cuadrox != None and cuadroy != None and not mouseClic:
				if self.logico.hayFichaJugador(cuadrox, cuadroy):
					# el mouse esta sobre un cuadro
					self.grafico.dibujarCuadroIluminado(cuadrox, cuadroy)
				elif self.logico.estaEnCamino(cuadrox, cuadroy) and seleccion:
					# el mouse esta sobre un cuadro del camino de la ficha
					self.grafico.dibujarCuadroIluminado(cuadrox, cuadroy, fichaSeleccion)
					# si esa posible jugada puede comer alguna ficha
					if self.logico.hayQueComer(cuadrox, cuadroy):
						self.grafico.dibujarAlerta(self.logico.getComer(), "roja")
					
			elif cuadrox != None and cuadroy != None and mouseClic:			
				if self.logico.hayFichaJugador(cuadrox, cuadroy):
					# mouse hizo clic sobre alguna ficha de turno
					self.logico.setCamino(cuadrox, cuadroy)
					self.grafico.dibujarCaminoIluminado(cuadrox, cuadroy)
					seleccion = True
					fichaSeleccion = (cuadrox, cuadroy)
					
				elif self.logico.estaEnCamino(cuadrox, cuadroy) and seleccion:
					# mouse hizo clic en una posicion del camino
					self.logico.mover(fichaSeleccion[0], fichaSeleccion[1], cuadrox, cuadroy)
					seleccion = False
					self.jugador.switchJugador()
			
					# estado del juego sin terminar
					copiaTablero = self.logico.getCopiaTablero()
					if self.calculos.verificarEsquinas(copiaTablero):
						# El rey ha llegado a una esquina
						print("El rey salio, las blancos han ganado.")
					else:
						encasillado = self.calculos.verificarLimites(copiaTablero)
						if encasillado == 4:
							# El rey ha sido encasillado, jaquemate
							print("El rey ha sido capturado, los negros ganan.")
						else:
							if encasillado == 3:
								# El rey puede estar en peligro
								if self.calculos.verificarPeligro(copiaTablero):
									# el rey esta en peligro
									self.grafico.dibujarAlerta(self.calculos.getPeligroRey(), "roja")
									peligro = True
							else:
								peligro = False
							
							if self.calculos.buscarEsquinaRey(copiaTablero):
								# hay una situacion de jaque o jaque mate
								self.grafico.dibujarAlerta(self.calculos.getEsquinas(), "verde")	
								jaque = True
							else:
								jaque = False
			
			pygame.display.update()	
			self.FPSCLOCK.tick(self.FPS)	
	
#############################################  Clase Grafico ##############################################
#                  Pinta la ventana conforme los datos proporcionados por la clase Logico                 # 
###########################################################################################################
class Grafico:

	# Asignacion de constantes
	LARGO_VENTANA = None
	ANCHO_VENTANA = None
	ANCHO_CUADRO = None
	LARGO_CUADRO = None
	TAMANO = None
	CENTRO = None
	MARGEN_X = None
	MARGEN_Y = None
	
	# almacenas las direcciones de las imagenes
	RUTA = None
	CARPETA = None
	DIRECCION = None
	IMAGENES = [None, None, None]
	
	# tuplas con las coordenadas de las posiciones de las fichas
	POSBX = None
	POSBY = None
	POSNX = None
	POSNY = None
	
	objFuente = None
	
	SUPERFICIE = None
	logico = None
	
	
	def __init__(self, logico, superficie, config):
		self.logico = logico
		self.SUPERFICIE = superficie
		self.LARGO_VENTANA = config["LARGO_VENTANA"]
		self.ANCHO_VENTANA = config["ANCHO_VENTANA"]
		self.TAMANO = config["TAMANO"]
		self.CENTRO = (self.TAMANO-1) / 2
		self.LARGO_CUADRO =  self.LARGO_VENTANA / self.TAMANO
		self.ANCHO_CUADRO =  self.ANCHO_VENTANA / self.TAMANO
		self.MARGEN_X = int(self.ANCHO_CUADRO*0.33)
		self.MARGEN_Y = self.ANCHO_CUADRO + int(self.ANCHO_CUADRO*0.33) 
		
		self.DIRECCION = ("rey.png","blanca.png","negra.png")
		self.CARPETA = ("img")
		self.RUTA = sys.argv[0][:len(sys.argv[0])-11]
		for i in range(3):
			self.IMAGENES[i] = pygame.image.load(os.path.join(self.RUTA, self.CARPETA, self.DIRECCION[i]))	
		self.IMAGENES = tuple(self.IMAGENES)
		self.POSBX = config["POSBX"]
		self.POSBY = config["POSBY"]
		self.POSNX = config["POSNX"]
		self.POSNY = config["POSNY"]
		
		self.objFuente = pygame.font.Font('freesansbold.ttf', 32)
		
		self.SUPERFICIE = pygame.display.set_mode(((self.LARGO_VENTANA + 2*self.MARGEN_X), (self.ANCHO_VENTANA + 2*self.MARGEN_Y) ))
		pygame.display.set_caption('Ajedrez Vikingo')
		
		
	""" Convierte las coordenadas de la esquina superior coordX del cuadro 
	a una coordenada de pixel.
	"""
	def coordEsquinaCuadro(self, cuadrox, cuadroy):
		coordX = self.MARGEN_X + (cuadroy * self.ANCHO_CUADRO)
		coordY = self.MARGEN_Y + (cuadrox * self.LARGO_CUADRO)
		return (coordX, coordY)
		

	""" Convierte las coordenadas del centro del cuadro a una coordenada de pixel. """
	def coordFichaEnCuadro(self, cuadrox, cuadroy, escalax, escalay):
		coordX, coordY = self.coordEsquinaCuadro(cuadrox, cuadroy)
		coordX += int((self.ANCHO_CUADRO - int(self.ANCHO_CUADRO * escalax)) / 2)
		coordY += int((self.LARGO_CUADRO - int(self.LARGO_CUADRO * escalay)) / 2)
		return (coordX, coordY)
		

	""" Recorre un tablero "imaginario" y devuelve una posicion si la coordenada
	en pixel esta dentro de algun cuadrado, en caso contrario devuelve la
	tupla (None, None).
	""" 	
	def getCuadroEnPixel(self, x, y):
		for cuadrox in range(self.TAMANO):
			for cuadroy in range(self.TAMANO):
				coordY, coordX = self.coordEsquinaCuadro(cuadrox, cuadroy)
				dibCuadro = pygame.Rect(coordY, coordX, self.LARGO_CUADRO, self.ANCHO_CUADRO)
				if dibCuadro.collidepoint(x, y):
					return (cuadrox, cuadroy)
		return (None, None)
		
		
	""" Dibuja los cuadros del tablero. """	
	def dibujarCuadros(self):
		for cuadrox in range(self.TAMANO):
			for cuadroy in range(self.TAMANO):
				coordX, coordY = self.coordEsquinaCuadro(cuadrox, cuadroy)
				pygame.draw.rect(self.SUPERFICIE, self.logico.getColorCuadro(cuadrox, cuadroy), 
					(coordX, coordY, self.LARGO_CUADRO, self.ANCHO_CUADRO))
		
	
	""" Dibuja el icono de una ficha. """
	def dibujarFicha(self, cuadrox, cuadroy, fichaEncima=""):
		if self.logico.getPos(cuadrox, cuadroy) == "rey" or fichaEncima == "rey":
			iconoParaDibujar = pygame.transform.smoothscale(self.IMAGENES[0], 
				(int(self.LARGO_CUADRO * 0.8), int(self.ANCHO_CUADRO * 0.75)))
			self.SUPERFICIE.blit(iconoParaDibujar, self.coordFichaEnCuadro(cuadrox, cuadroy, 0.8, 0.75))
				
		elif self.logico.getPos(cuadrox, cuadroy) == "sueco" or fichaEncima == "sueco":
			iconoParaDibujar = pygame.transform.smoothscale(self.IMAGENES[1], 
				(int(self.LARGO_CUADRO * 0.5), int(self.ANCHO_CUADRO * 0.75)))
			self.SUPERFICIE.blit(iconoParaDibujar, self.coordFichaEnCuadro(cuadrox, cuadroy, 0.5, 0.75))
		
		elif self.logico.getPos(cuadrox, cuadroy) == "moscovita" or fichaEncima == "moscovita":
			iconoParaDibujar = pygame.transform.smoothscale(self.IMAGENES[2], 
				(int(self.LARGO_CUADRO * 0.5), int(self.ANCHO_CUADRO * 0.75)))
			self.SUPERFICIE.blit(iconoParaDibujar, self.coordFichaEnCuadro(cuadrox, cuadroy, 0.5, 0.75))	
		
		
	""" Dibuja las fichas del tablero. """
	def dibujarFichas(self):		
		for cuadrox in range(self.TAMANO):
			for cuadroy in range(self.TAMANO):
				self.dibujarFicha(cuadrox, cuadroy)
					

	""" Vuelve a dibujar el cuadro señalado por los parámetros pero de un color más claro. """
	def dibujarCuadroIluminado(self, cuadrox, cuadroy, fichaEncima=(), alerta=""):
		coordY, coordX = self.coordEsquinaCuadro(cuadrox, cuadroy)
		if alerta != "":
			pygame.draw.rect(self.SUPERFICIE, self.logico.getColorAlerta(alerta), 
				(coordY, coordX, self.LARGO_CUADRO, self.ANCHO_CUADRO))
		else:
			pygame.draw.rect(self.SUPERFICIE, self.logico.getColorIluminado(cuadrox, cuadroy), 
				(coordY, coordX, self.LARGO_CUADRO, self.ANCHO_CUADRO))
		if fichaEncima != ():
			self.dibujarFicha(cuadrox, cuadroy, self.logico.getPos(fichaEncima[0], fichaEncima[1]))
		else:
			self.dibujarFicha(cuadrox, cuadroy)
		
		
	""" Dibuja el camino iluminado de la ficha seleccionada. """	
	def dibujarCaminoIluminado(self, cuadrox, cuadroy):
		camino = self.logico.getCamino()
		if cuadrox != None and cuadroy != None: 
			self.dibujarCuadroIluminado(cuadrox, cuadroy)
		for cuadro in camino:
			self.dibujarCuadroIluminado(cuadro[0], cuadro[1])
		
		
	""" Dibuja un color de alerta en los cuadros indicados por 
	la lista retornada por logico.getComer().
	"""
	def dibujarAlerta(self, listaCuadros, alerta):
		for cuadro in listaCuadros:
			self.dibujarCuadroIluminado(cuadro[0], cuadro[1], (), alerta)
	
	
	""" Dibuja los iconos de los paneles superior e inferior del tablero de juego. """
	def dibujarPanel(self):
		coordX = self.MARGEN_X + int((self.ANCHO_CUADRO - int(self.ANCHO_CUADRO * 0.50)) / 2)
		coordY = 0 + int((self.LARGO_CUADRO - int(self.LARGO_CUADRO * 0.75)) / 2)
		
		iconoParaDibujar = pygame.transform.smoothscale(self.IMAGENES[1], 
			(int(self.LARGO_CUADRO * 0.50), int(self.ANCHO_CUADRO * 0.75)))
		self.SUPERFICIE.blit(iconoParaDibujar, (coordX, coordY))
		
		coordX = self.MARGEN_X + int((self.ANCHO_CUADRO - int(self.ANCHO_CUADRO * 0.50)) / 2)
		coordY = (self.ANCHO_VENTANA + self.MARGEN_X + self.MARGEN_Y) + int((self.LARGO_CUADRO - int(self.LARGO_CUADRO * 0.75)) / 2)
		
		iconoParaDibujar = pygame.transform.smoothscale(self.IMAGENES[2], 
			(int(self.LARGO_CUADRO * 0.50), int(self.ANCHO_CUADRO * 0.75)))
		self.SUPERFICIE.blit(iconoParaDibujar, (coordX, coordY))

		
	def dibujarTurno(self):
		
		coordX = self.MARGEN_X + self.LARGO_CUADRO + int((self.ANCHO_CUADRO - int(self.ANCHO_CUADRO * 0.50)) / 2)
		coordY = int(self.ANCHO_CUADRO / 2)
		
		superfTexto = self.objFuente.render('Hello world!', True, (255,255,255))
		rectTexto = superfTexto.get_rect()
		rectTexto.left = coordX
		rectTexto.centery = coordY
		self.SUPERFICIE.blit(superfTexto, rectTexto)
		
	""" Dibuja los cuadros y las fichas del tablero. """	
	def dibujarVentana(self):
		self.SUPERFICIE.fill(self.logico.getColorFondo())
		pygame.draw.rect(self.SUPERFICIE, self.logico.getColorMargenes(), (0, self.ANCHO_CUADRO, (self.LARGO_VENTANA + 2*self.MARGEN_X), (self.ANCHO_VENTANA + 2*self.MARGEN_X)), 0)
		
		self.dibujarPanel()
		self.dibujarTurno()
		self.dibujarCuadros()
		self.dibujarFichas()
			
########################################### Clase Logico ##################################################	
#         Maneja los datos y la lógica del juego, formada por las clases Tablero y Calculos               #
###########################################################################################################	
class Logico:
    #                      R    G    B
	COLOR1             = ( 80,  48,  34)
	COLOR2             = (203, 173, 112)
	COLOR_CLARO1       = (140, 108,  94)
	COLOR_CLARO2       = (255, 233, 172)
	COLOR_ALERTA_ROJA  = (248,  55,  47)
	COLOR_ALERTA_VERDE = ( 55, 200,  47)
	COLOR_MARGEN       = ( 75,  43,  29)
	
	# almacenaran las instancias de clase
	jugador = None
	tablero = None
	calculos = None
	
	def __init__(self, jug, tabl, calc, config):
		self.jugador = jug
		self.tablero = tabl
		self.calculos = calc
		self.crearTablero()
		
	# Operaciones que interactuan con la clase Tablero #
	
	""" Crea una matriz que representa la lógica del tablero. """	
	def crearTablero(self):
		self.tablero.crearTablero()

			
	""" Devuelve una copia de la matriz. """
	def getCopiaTablero(self):
		return self.tablero.getCopiaTablero()

		
	""" Devuelve una posición de la matriz. """
	def getPos(self, cuadrox, cuadroy):
		return self.tablero.getPos(cuadrox, cuadroy)

		
	""" Devuelve True si el cuadro indicado coresponde a una ficha de turno. """
	def hayFichaJugador(self, cuadrox, cuadroy):
		return self.tablero.hayFichaJugador(cuadrox, cuadroy)
		
	""" Calcula si hay posibles fichas para comer dada una determinada posición
	devuelve True si hay al menos una.
	"""
	def hayQueComer(self, cuadrox, cuadroy):
		return self.tablero.comerFicha(cuadrox, cuadroy)
	
	
	""" Devuelve la lista con las posiciones para comer. """
	def getComer(self):
		return self.tablero.getComer()
	
	
	""" Mueve una ficha del tablero y busca si hay fichas para comer. """
	def mover(self, cx, cy, cnx, cny):
		self.tablero.setFicha(cx, cy, cnx, cny)
		if self.tablero.comerFicha(cnx, cny):
			for cuadro in self.getComer():
				self.tablero.setFicha(cuadro[0], cuadro[1])	
	
		# Operaciones que interactúan con la clase Calculos #
	
	""" Dada una posicion calcula el "camino" que esa ficha puede recorrer. """
	def setCamino(self, cuadrox, cuadroy):
		self.calculos.setCamino(self.getCopiaTablero(), cuadrox, cuadroy)
		
	
	""" Retorna la lista con los cuadros del camino de la ficha. """	
	def getCamino(self):
		return self.calculos.getCamino()
		
	
	""" Devuelve True si la posición indicada por los parametros forma parte de la lista
	actual del "camino". 
	"""	
	def estaEnCamino(self, cuadrox, cuadroy):
		return self.calculos.estaEnCamino(cuadrox, cuadroy)
		

	# Funciones que retornan colores en formato RGB #

	""" Devuelve el color de fondo del tablero. """
	def getColorFondo(self):
		return self.COLOR1	
		
	def getColorMargenes(self):
		return self.COLOR_MARGEN
	
	""" Devuelve los colores del tablero por defecto. """
	def getColorCuadro(self, x, y):
		if x % 2 == 0:
			if y % 2 == 0:
				return self.COLOR1
			else:
				return self.COLOR2
		else:
			if y % 2 == 0:
				return self.COLOR2
			else:
				return self.COLOR1
		
		
	""" Devuelve los colores de los cuadros iluminados. """
	def getColorIluminado(self, x, y):
		if x % 2 == 0:
			if y % 2 == 0:
				return self.COLOR_CLARO1
			else:
				return self.COLOR_CLARO2
		else:
			if y % 2 == 0:
				return self.COLOR_CLARO2
			else:
				return self.COLOR_CLARO1
		
		
	""" Devuelve el color de alerta. """	
	def getColorAlerta(self, alerta):
		if alerta == "roja":
			return self.COLOR_ALERTA_ROJA
		elif alerta == "verde":
			return self.COLOR_ALERTA_VERDE

########################################### Clase Tablero #################################################	
#                        Maneja la representación y los cambios del tablero de juego.                     #
###########################################################################################################				
class Tablero:
	
	TAMANO = None
	CENTRO = None
	
	POSBX = None
	POSBY = None
	POSNX = None
	POSNY = None

	tablero = None
	listaComer = None
	
	jugador = None
	
	def __init__(self, jug, config):
		self.jugador = jug
		self.TAMANO = config["TAMANO"]
		self.CENTRO = (self.TAMANO-1) / 2
		
		self.POSBX = config["POSBX"]
		self.POSBY = config["POSBY"]
		self.POSNX = config["POSNX"]
		self.POSNY = config["POSNY"]
	
	""" Crea una matriz que representa la lógica del tablero """	
	def crearTablero(self):
		self.tablero = []
		for x in range(self.TAMANO):
			columna = []
			for y in range(self.TAMANO):
				columna.append("")
			self.tablero.append(columna)
		
		# Coloca en los lugares correspondiente la representacion de las fichas.		
		self.tablero[self.CENTRO][self.CENTRO] = "rey"
		
		for i in range(len(self.POSBX)):
			self.tablero[self.POSBX[i]][self.POSBY[i]] = "sueco"
			
		for i in range(len(self.POSNX)):
			self.tablero[self.POSNX[i]][self.POSNY[i]] = "moscovita"
		
			
	""" Devuelve una copia de la matriz. """
	def getCopiaTablero(self):
		return deepcopy(self.tablero)

		
	""" Mueve una posicion del tablero a otra, dejando la primera en blanco. """	
	def setFicha(self, cuadrox, cuadroy, cnx=None, cny=None):
		if cnx == None:
			self.tablero[cuadrox][cuadroy] = ""
		else:
			self.tablero[cnx][cny] = self.tablero[cuadrox][cuadroy]
			self.tablero[cuadrox][cuadroy] = ""
		
		
	""" Devuelve una posición de la matriz. """
	def getPos(self, cuadrox, cuadroy):
		return self.tablero[cuadrox][cuadroy]

		
	""" Devuelve True si el cuadro indicado coresponde a una ficha de turno. """
	def hayFichaJugador(self, cuadrox, cuadroy):
		if self.jugador.getJugador() == "jugador1":
			if self.tablero[cuadrox][cuadroy] == "moscovita":
				return True
			else:
				return False
		else:
			if self.tablero[cuadrox][cuadroy] == "rey" or self.tablero[cuadrox][cuadroy] == "sueco":
				return True
			else:
				return False
				
		
	""" Calcula si hay posibles fichas para comer dada una determinada posición
	devuelve True si hay al menos una.
	"""		
	def comerFicha(self, cuadrox, cuadroy):
		self.listaComer = []
		if self.jugador.getJugador() == "jugador1":
			oponente = "sueco"
			aliado = "moscovita"
		else:
			oponente = "moscovita"
			aliado = "sueco"
			
		b = False
		
		# esquinas
		if cuadrox == 0 and cuadroy == 2 and self.tablero[0][1] == oponente:
			self.listaComer.append((0,1))
			b = True
		elif cuadrox == 0 and cuadroy == self.TAMANO-3 and self.tablero[0][self.TAMANO-2] == oponente:
			self.listaComer.append((0,self.TAMANO-2))
			b = True
		elif cuadrox == self.TAMANO-1 and cuadroy == 2 and self.tablero[self.TAMANO-1][1] == oponente:
			self.listaComer.append((self.TAMANO-1,1))
			b = True
		elif cuadrox == self.TAMANO-1 and cuadroy == self.TAMANO-3 and self.tablero[self.TAMANO-1][self.TAMANO-2] == oponente:
			self.listaComer.append((self.TAMANO-1,self.TAMANO-2))
			b = True
		elif cuadrox == 2 and cuadroy == 0 and self.tablero[1][0] == oponente:
			self.listaComer.append((1,0))
			b = True
		elif cuadrox == self.TAMANO-3 and cuadroy == 0 and self.tablero[self.TAMANO-2][0] == oponente:
			self.listaComer.append((self.TAMANO-2,0))
			b = True
		elif cuadrox == 2 and cuadroy == self.TAMANO-1 and self.tablero[1][self.TAMANO-1] == oponente:
			self.listaComer.append((1,self.TAMANO-1))
			b = True	
		elif cuadrox == self.TAMANO-3 and cuadroy == self.TAMANO-1 and self.tablero[self.TAMANO-2][self.TAMANO-1] == oponente:
			self.listaComer.append((self.TAMANO-2,self.TAMANO-1))
			b = True
			
		# limites
		if cuadrox > 1:
			#busque coordY
			if self.tablero[cuadrox-1][cuadroy] == oponente:
				if self.tablero[cuadrox-2][cuadroy] == aliado:
					self.listaComer.append((cuadrox-1, cuadroy))
					b = True
		if cuadroy > 1:		
			# busque a la coordX
			if self.tablero[cuadrox][cuadroy-1] == oponente:
				if self.tablero[cuadrox][cuadroy-2] == aliado:
					self.listaComer.append((cuadrox,cuadroy-1))
					b = True;
		if cuadrox < self.TAMANO-3:
			# busque abajo
			if self.tablero[cuadrox+1][cuadroy] == oponente:
				if self.tablero[cuadrox+2][cuadroy] == aliado:
					self.listaComer.append((cuadrox+1,cuadroy))
					b = True
		if cuadroy < self.TAMANO-3:
			# busque a la derecha
			if self.tablero[cuadrox][cuadroy+1] == oponente:
				if self.tablero[cuadrox][cuadroy+2] == aliado:
					self.listaComer.append((cuadrox,cuadroy+1))
					b = True;
		return b;
		
		
	""" Devuelve la lista con las posiciones para comer. """		
	def getComer(self):
		return self.listaComer	
	
########################################### Clase Calculos ################################################	
#                         Realiza los calculos necesarios conforme al tablero                             #
###########################################################################################################	
class Calculos:
	TAMANO = None
	CENTRO = None
	
	camino = None
	esquinas = None
	limitesRey = None
	peligroRey = None
	
	def __init__(self, config):
		self.camino = []
		self.TAMANO = config["TAMANO"]
		self.CENTRO = (self.TAMANO-1) / 2
		
		
	#   Operaciones para el calculo del camino de una ficha    #
	
		""" Devuelve True si no hay ficha en un cuadro. """	
	def noHayFicha(self, tablero, cuadrox, cuadroy, NoEsRey):
		if NoEsRey and cuadrox == self.CENTRO and cuadroy == self.CENTRO:
			return False
		elif tablero[cuadrox][cuadroy] == "":
			return True
		else:
			return False
			
			
	""" Si el cuadro indicado esta dentro de la lista de camino, True """
	def estaEnCamino(self, cuadrox, cuadroy):
		for cuadro in self.camino:
			if cuadro == (cuadrox, cuadroy):
				return True
		return False

		
	""" Devuelve la lista de camino actual """
	def getCamino(self):
		return self.camino
		
		
	""" Dada una posicion de ficha busca los posibles lugares donde esta se puede mover. """
	def setCamino(self, tablero, cuadrox, cuadroy):
		copiaTablero = tablero
		self.camino = []
		NoEsRey = True
		if tablero[cuadrox][cuadroy] == "rey":
			NoEsRey = False
		
		# verifique a la derecha
		c = cuadrox + 1
		while c < self.TAMANO and self.noHayFicha(copiaTablero, c, cuadroy, NoEsRey):
			self.camino.append( (c, cuadroy) )
			c+=1
		# verifique a la coordX
		c = cuadrox - 1
		while c >= 0 and self.noHayFicha(copiaTablero, c, cuadroy, NoEsRey):
			self.camino.append( (c, cuadroy) )
			c-=1
		# verifique abajo
		c = cuadroy + 1
		while c < self.TAMANO and self.noHayFicha(copiaTablero, cuadrox, c, NoEsRey):
			self.camino.append( (cuadrox, c) )
			c+=1
		# verifique coordY
		c = cuadroy - 1
		while c >= 0 and self.noHayFicha(copiaTablero, cuadrox, c, NoEsRey):
			self.camino.append( (cuadrox, c) )
			c-=1
			
		if copiaTablero[cuadrox][cuadroy] != "rey":
			# Si la ficha no es la del rey hay que eliminar como posible lugar para mover las esquinas
			if (0,0) in self.camino: self.camino.remove((0,0))		
			if (0, self.TAMANO-1) in self.camino: self.camino.remove((0, self.TAMANO-1))	
			if (self.TAMANO-1, 0) in self.camino: self.camino.remove((self.TAMANO-1, 0))	
			if (self.TAMANO-1, self.TAMANO-1) in self.camino: self.camino.remove((self.TAMANO-1, self.TAMANO-1))	
		
		return self.camino

		
	"""       Operaciones para calcular el estado del rey.     """ 
		
	""" Buscan en el tablero la ficha del rey y devuelve su posicion. """
	def buscarRey(self, copiaTablero):
		for i in range(self.TAMANO):
			for j in range(self.TAMANO):
				if copiaTablero[i][j] == "rey":
					return (i, j)
	
			
	""" Determina si el rey ha llegado a alguna esquina del tablero """		
	def verificarEsquinas(self, copiaTablero):
		tablero = copiaTablero
		if tablero[0][0] == "rey" or tablero[0][self.TAMANO-1] == "rey" or tablero[self.TAMANO-1][0] == "rey" or tablero[self.TAMANO-1][self.TAMANO-1] == "rey":
			return True
		else:
			return False
			
			
	""" Crea una tupla que representa los limites del rey para determinar 
	si este esta encasillado.
	"""
	def verificarLimites(self, copiaTablero):
		tablero = copiaTablero
		posRey = self.buscarRey(tablero)
		
		# derecha, coordX, coordY, abajo
		self.limitesRey = [0, 0, 0, 0]
		
		# esquinas
		if posRey == (0, self.TAMANO-2) or posRey == (self.TAMANO-1, self.TAMANO-2):
			self.limitesRey[0] = 1
		elif posRey == (0, 1) or posRey == (self.TAMANO-1, 1):		
			self.limitesRey[1] = 1
		elif posRey == (1, 0) or posRey == (1, self.TAMANO-1):
			self.limitesRey[2] = 1
		elif posRey == (self.TAMANO-2, 0) or posRey == (self.TAMANO-2, self.TAMANO-1):
			self.limitesRey[3] = 1	
			
		limites = ( 
		(0, posRey[1], self.TAMANO-1, (self.CENTRO, self.CENTRO-1), posRey[0], posRey[1]+1, posRey[0], posRey[1]+2),
		(1, posRey[1], 0, (self.CENTRO, self.CENTRO+1), posRey[0], posRey[1]-1, posRey[0], posRey[1]-2),
		(2, posRey[0], 0, (self.CENTRO+1, self.CENTRO), posRey[0]-1, posRey[1], posRey[0]-2, posRey[1]),
		(3, posRey[0], self.TAMANO-1, (self.CENTRO-1, self.CENTRO), posRey[0]+1, posRey[1], posRey[0]+2, posRey[1]) )
		
		for lim in limites:
			if lim[1] == lim[2]:
				# esta en una orilla
				self.limitesRey[lim[0]] = 1
			elif posRey == lim[3]:
				# esta al lado del centro del tablero
				self.limitesRey[lim[0]] = 1
			elif tablero[lim[4]][lim[5]] == "sueco" and tablero[lim[6]][lim[7]] == "moscovita":
				# tiene una ficha blanca seguida de una negra a la par
				self.limitesRey[lim[0]] = 1
			elif tablero[lim[4]][lim[5]] == "moscovita":
				# tiene una ficha negra a la par 
				self.limitesRey[lim[0]] = 1
				
		print(self.limitesRey)
		# sumatoria para control
		return self.limitesRey[0] + self.limitesRey[1] + self.limitesRey[2] + self.limitesRey[3]


	""" Determina si hay peligro en el unico limite libre de rey """	
	def verificarPeligro(self, copiaTablero):
		posRey = self.buscarRey(copiaTablero)
		self.peligroRey = []
		limite = -1
		for i in range(4):
			if self.limitesRey[i] == 0:
				limite = i
		
		if limite == 0:
			# derecha
			x = posRey[0]
			y = posRey[1]+1
			
			control = x
			while control >= 0 and copiaTablero[control][y] != "sueco":
				if copiaTablero[control][y] == "moscovita":
					self.peligroRey.append( (control, y) ) 
					control = 0 # truco malvado para parar el while con el primer negro que encuentre
				control -= 1
		
			control = x
			while control <= self.TAMANO-1 and copiaTablero[control][y] != "sueco":
				if copiaTablero[control][y] == "moscovita":
					self.peligroRey.append( (control, y) )
					control = self.TAMANO-1
				control += 1
			
			control = y
			while control <= self.TAMANO-1 and copiaTablero[x][control] != "sueco":
				if copiaTablero[x][control] == "moscovita":
					self.peligroRey.append( (x, control) )
					control = self.TAMANO-1
				control += 1

		if limite == 1:
			# coordX
			x = posRey[0]
			y = posRey[1]-1
			
			control = y
			while control >= 0 and copiaTablero[x][control] != "sueco":
				if copiaTablero[x][control] == "moscovita":
					self.peligroRey.append( (x, control) )
					control = 0
				control -= 1

			control = x
			while control >= 0 and copiaTablero[control][y] != "sueco":
				if copiaTablero[control][y] == "moscovita":
					self.peligroRey.append( (control, y) )
					control = 0
				control -= 1
				
			control = x
			while control <= self.TAMANO-1 and copiaTablero[control][y] != "sueco":
				if copiaTablero[control][y] == "moscovita":
					self.peligroRey.append( (control, y) )
					control = self.TAMANO-1
				control += 1
			
		if limite == 2:
			# coordY
			x = posRey[0]-1
			y = posRey[1]
			
			control = y
			while control >= 0 and copiaTablero[x][control] != "sueco":
				if copiaTablero[x][control] == "moscovita":
					self.peligroRey.append( (x, control) )
					control = 0
				control -= 1
				
			control = x
			while control >= 0 and copiaTablero[control][y] != "sueco":
				if copiaTablero[control][y] == "moscovita":
					self.peligroRey.append( (control, y) )
					control = 0
				control -= 1
				
			control = y
			while control <= self.TAMANO-1 and copiaTablero[x][control] != "sueco":
				if copiaTablero[x][control] == "moscovita":
					self.peligroRey.append( (x, control) )
					control = self.TAMANO-1
				control += 1

		if limite == 3:
			#abajo
			x = posRey[0]+1
			y = posRey[1]
			
			control = y
			while control >= 0 and copiaTablero[x][control] != "sueco":
				if copiaTablero[x][control] == "moscovita":
					self.peligroRey.append( (x, control) )
					control = 0
				control -= 1
				
			control = x
			while control <= self.TAMANO-1 and copiaTablero[control][y] != "sueco":
				if copiaTablero[control][y] == "moscovita":
					self.peligroRey.append( (control, y) )
					control = self.TAMANO-1
				control += 1
				
			control = y
			while control <= self.TAMANO-1 and copiaTablero[x][control] != "sueco":
				if copiaTablero[x][control] == "moscovita":
					self.peligroRey.append( (x, control) )
					control = self.TAMANO-1
				control += 1
				
		if self.peligroRey != []:
			return True
		else:
			return False
				
				
	""" Devuelve la lista con las fichas a iluminar """	
	def getPeligroRey(self):
		return self.peligroRey
		
		
	""" Determina si en el camino del rey esta alguna esquina. """
	def buscarEsquinaRey(self, copiaTablero):
		rey = self.buscarRey(copiaTablero)
		self.esquinas = []
		
		cx = rey[0]-1
		cy = rey[1]
		while(cx >= 0 and copiaTablero[cx][cy]== ""):
			# revisar coordY
			if( (cx == 0 and cy == 0) or (cx == 0 and cy == self.TAMANO-1) ):
				self.esquinas.append( (cx, cy) )
			cx -= 1

		cx = rey[0]+1
		cy = rey[1]
		while(cx <= self.TAMANO-1 and copiaTablero[cx][cy]== ""):
			# revisar abajo
			if( (cx == self.TAMANO-1 and cy == 0) or (cx == self.TAMANO-1 and cy == self.TAMANO-1) ):
				self.esquinas.append( (cx, cy) )
			cx += 1
		
		cx = rey[0]
		cy = rey[1]-1
		while(cy >= 0 and copiaTablero[cx][cy]== ""):
			# revisar a la coordX
			if( (cx == 0 and cy == 0) or (cx == self.TAMANO-1 and cy == 0) ):
				self.esquinas.append( (cx, cy) )
			cy -= 1
			
		cx = rey[0]
		cy = rey[1]+1
		while(cy <= self.TAMANO-1):
			# revisar a la derecha
			if( (cx == 0 and cy == self.TAMANO-1) or (cx == self.TAMANO-1 and cy == self.TAMANO-1) ):
				self.esquinas.append( (cx, cy) )
			cy += 1
		
		if self.esquinas != []:	
			# si hay al menos una esquina alcanzable
			return True
		else:
			return False	
	
	""" Devuelve una lista con las esquinas alcanzables por el rey """
	def getEsquinas(self):
		return self.esquinas
	
########################################### Clase Jugador #################################################	
#                    Por ahora, mantiene la informacion sobre el jugador de turno                         #
###########################################################################################################	
class Jugador:

	jugador1 = "jugador1"
	jugador2 = "jugador2"
	
	jugadorActual = None
	
	def __init__(self):
		self.jugadorActual = self.jugador1
		
	def switchJugador(self):
		if self.jugadorActual == self.jugador1:
			self.jugadorActual = self.jugador2
		else:
			self.jugadorActual = self.jugador1
			
	def getJugador(self):
		return self.jugadorActual
		
	
if __name__ == '__main__':
	config = {}
	execfile("settings.config", config) 
	main = Main(config)
	main.iniciar()
