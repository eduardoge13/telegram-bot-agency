export type Locale = 'es' | 'en';

export const brand = {
	name: 'Blue Sky Travel',
	tagline: {
		es: 'Planificación de viajes premium con una experiencia que convierte mejor.',
		en: 'Premium travel planning with a sharper, conversion-ready experience.',
	},
	website: 'https://blueskytravelmx.com',
	productionDomain: 'blueskytravelmx.com',
	stagingDomain: 'blueskytravelmx.online',
	redirectDomain: 'blueskytravelmx.info',
	whatsappDisplay: '+52 81 4821 7361',
	whatsappE164: '528148217361',
	privacyEmail: 'privacy@blueskytravelmx.com',
	salesEmail: 'hola@blueskytravelmx.com',
	legalEntity: 'Blue Sky Travel [replace with legal entity before production]',
	legalAddress: '[replace with business address before production]',
	lastUpdated: 'April 3, 2026',
	legalReviewRequired: true,
};

const whatsappMessages: Record<Locale, string> = {
	es: 'Hola, quiero planear un viaje con Blue Sky Travel.',
	en: 'Hello, I want to plan a trip with Blue Sky Travel.',
};

export const whatsappHref = (locale: Locale) =>
	`https://wa.me/${brand.whatsappE164}?text=${encodeURIComponent(whatsappMessages[locale])}`;

export const dealWhatsappHref = (
	locale: Locale,
	cityName: string,
	priceFrom?: number,
	priceTo?: number,
	currency?: string,
) => {
	// Carry the whole band into the chat, never the floor alone: a lead who opens
	// WhatsApp with a single exact figure in writing expects that figure back.
	const priceLine =
		priceFrom && priceTo && currency
			? locale === 'es'
				? ` Vi el rango de referencia de $${priceFrom.toLocaleString('es-MX')} a $${priceTo.toLocaleString('es-MX')} ${currency} por persona.`
				: ` I saw the reference range of $${priceFrom.toLocaleString('en-US')} to $${priceTo.toLocaleString('en-US')} ${currency} per person.`
			: '';
	const text =
		locale === 'es'
			? `Hola, quiero cotizar un viaje a ${cityName}.${priceLine} ¿Me ayudan?`
			: `Hi, I want to get a quote for a trip to ${cityName}.${priceLine} Can you help me?`;
	return `https://wa.me/${brand.whatsappE164}?text=${encodeURIComponent(text)}`;
};

export const localizedPaths = {
	home: {
		es: '/',
		en: '/en/',
	},
	privacy: {
		es: '/privacy-policy',
		en: '/en/privacy-policy',
	},
	terms: {
		es: '/terms',
		en: '/en/terms',
	},
	dataDeletion: {
		es: '/data-deletion',
		en: '/en/data-deletion',
	},
} as const;

export const legalWarning = {
	es: 'Aviso de implementación: antes del corte a producción y del cambio de Meta a Live, sustituye el nombre legal, domicilio y correos de privacidad por los definitivos.',
	en: 'Implementation notice: before production cutover and switching Meta to Live, replace the legal name, address, and privacy contact emails with the final business details.',
};

export const homeContent = {
	es: {
		title: 'Blue Sky Travel | Vuelos y viajes premium por WhatsApp',
		description:
			'Encuentra las mejores tarifas a Europa y destinos de playa, y arma tu viaje directo por WhatsApp con un agente bilingüe. Precios verificados a diario.',
		nav: [
			{ label: 'Destinos', href: '#deals' },
			{ label: 'Servicios', href: '#services' },
			{ label: 'Cómo funciona', href: '#process' },
			{ label: 'FAQ', href: '#faq' },
		],
		languageLabel: 'EN',
		languageHref: localizedPaths.home.en,
		hero: {
			eyebrow: 'Vuelos y viajes a tu medida, sin escalas de por medio',
			headline: '¿A dónde te llevamos? Elige un destino y cotiza por WhatsApp en segundos.',
			body:
				'Monitoreamos tarifas de aerolíneas todos los días para que tu viaje a Europa, el Caribe o donde sea salga a buen precio. Elige un destino, te armamos la ruta y cerramos todo por WhatsApp.',
			primaryCta: 'Cotizar por WhatsApp',
			secondaryCta: 'Ver destinos y precios',
			trustBadges: ['Precios revisados a diario', 'Atención bilingüe', 'Respuesta en minutos por WhatsApp'],
		},
		dealsHeading: {
			eyebrow: 'Destinos con buen precio ahora',
			title: 'Tarifas reales, monitoreadas todos los días.',
			body: 'Estos son los rangos por persona que hemos visto en las últimas semanas: del vuelo más barato al precio típico. Elige un destino y te cotizamos tu fecha exacta por WhatsApp.',
			ctaLabel: 'Cotizar este destino',
			updatedPrefix: 'Precios actualizados el',
			sampleSuffix: 'tarifas monitoreadas',
			rangeLabel: 'Por persona, rango de referencia',
			rangeNote: 'Rango de referencia sujeto a disponibilidad y fechas.',
			fallbackTitle: '¿No ves tu destino?',
			fallbackBody: 'Cotizamos cualquier ruta, no solo las que están en la lista.',
			fallbackCta: 'Preguntar por otro destino',
		},
		servicesHeading: {
			eyebrow: 'En qué te ayudamos',
			title: 'Un viaje, muchas formas de necesitarlo.',
			body: 'Así sea trabajo, luna de miel o vacaciones familiares, coordinamos vuelos, hospedaje y el ritmo del viaje contigo.',
		},
		services: [
			{
				title: 'Escapadas y vacaciones',
				body: 'Playa, ciudad o Europa: armamos vuelos y hospedaje con buen precio y sin perder comodidad.',
			},
			{
				title: 'Viaje de negocios',
				body: 'Itinerarios rápidos de coordinar, con horarios que respetan tu agenda de trabajo.',
			},
			{
				title: 'Bodas, aniversarios y celebraciones',
				body: 'Fechas importantes con más cuidado en el detalle: hospedaje, transporte y ocasiones especiales.',
			},
			{
				title: 'Atención en español e inglés',
				body: 'Coordinamos tu viaje en el idioma que prefieras, ideal para grupos o familias mixtas.',
			},
		],
		processHeading: {
			eyebrow: 'Cómo funciona',
			title: 'De la idea al boleto, en cuatro pasos por WhatsApp.',
			body: 'Sin formularios largos ni portales confusos. Todo se resuelve en la conversación.',
		},
		process: [
			{
				step: '01',
				title: 'Nos escribes por WhatsApp',
				body: 'Cuéntanos destino, fechas aproximadas y cuántos viajan. Con un clic en cualquier destino de arriba ya lo hicimos por ti.',
			},
			{
				step: '02',
				title: 'Te mandamos opciones reales',
				body: 'Buscamos tarifas vigentes con aerolíneas y te mandamos las mejores combinaciones de precio y horario.',
			},
			{
				step: '03',
				title: 'Confirmas y coordinamos el resto',
				body: 'Hospedaje, traslados y cualquier detalle extra se acomoda a tu presupuesto y prioridad.',
			},
			{
				step: '04',
				title: 'Viajas con el itinerario en la mano',
				body: 'Te dejamos toda la información clara antes de salir, y seguimos disponibles por si algo cambia.',
			},
		],
		trustHeading: {
			eyebrow: 'Por qué reservar con nosotros',
			title: 'Lo que puedes verificar tú mismo antes de escribirnos.',
			body: 'Nada de promesas vacías: esto es lo que realmente hacemos distinto.',
		},
		trust: [
			{
				title: 'Monitoreo diario de tarifas',
				body: 'Revisamos precios de vuelo constantemente para avisarte cuando conviene comprar.',
			},
			{
				title: 'Todo por WhatsApp, sin vueltas',
				body: 'Nada de portales ni cuentas que crear. Cotizas, confirmas y viajas desde el chat.',
			},
			{
				title: 'Transparencia legal desde el sitio',
				body: 'Aviso de privacidad, términos y contacto directo disponibles siempre en el pie de página.',
			},
		],
		faqHeading: {
			eyebrow: 'Preguntas frecuentes',
			title: 'Antes de escribirnos, esto puede ayudarte.',
			body: '',
		},
		faq: [
			{
				question: '¿Los precios que veo en el sitio son reales?',
				answer:
					'Sí. Cada rango sale de las tarifas por persona que detectamos para esa ruta en las últimas semanas: el primer número es el vuelo más barato que vimos y el segundo es el precio típico. Tu precio final depende de tu fecha exacta, por eso confirmamos todo por WhatsApp antes de cobrar cualquier cosa.',
			},
			{
				question: '¿Atienden en inglés?',
				answer: 'Sí, coordinamos tu viaje en español o inglés, lo que te sea más cómodo.',
			},
			{
				question: '¿Puedo cotizar un destino que no está en la lista?',
				answer: 'Claro. La lista muestra los destinos con mejor precio ahora mismo, pero cotizamos cualquier ruta que necesites.',
			},
			{
				question: '¿Cómo sé que mis datos están protegidos?',
				answer: 'Nuestro aviso de privacidad explica qué información usamos y para qué. Puedes consultarlo desde el pie de página en cualquier momento.',
			},
		],
		cta: {
			title: '¿Ya sabes a dónde quieres ir?',
			body: 'Escríbenos por WhatsApp y en minutos tienes opciones reales de vuelo para tu próximo viaje.',
			primary: 'Cotizar mi viaje',
			secondary: 'Leer aviso de privacidad',
		},
		footer: {
			blurb:
				'Planeación de viajes bilingüe con tarifas monitoreadas a diario y coordinación directa por WhatsApp.',
			legal: 'Legal',
			privacy: 'Privacidad',
			terms: 'Términos',
			dataDeletion: 'Eliminación de datos',
		},
	},
	en: {
		title: 'Blue Sky Travel | Flights and premium trips over WhatsApp',
		description:
			'Find the best fares to Europe and beach destinations, and plan your trip directly over WhatsApp with a bilingual agent. Prices checked daily.',
		nav: [
			{ label: 'Destinations', href: '#deals' },
			{ label: 'Services', href: '#services' },
			{ label: 'How it works', href: '#process' },
			{ label: 'FAQ', href: '#faq' },
		],
		languageLabel: 'ES',
		languageHref: localizedPaths.home.es,
		hero: {
			eyebrow: 'Flights and trips built around you, no middlemen',
			headline: 'Where to? Pick a destination and get a quote on WhatsApp in seconds.',
			body:
				'We track airline fares every day so your trip to Europe, the Caribbean, or anywhere else lands at a fair price. Pick a destination, we build the route, and we close everything over WhatsApp.',
			primaryCta: 'Get a quote on WhatsApp',
			secondaryCta: 'See destinations and prices',
			trustBadges: ['Prices checked daily', 'Bilingual support', 'Replies in minutes on WhatsApp'],
		},
		dealsHeading: {
			eyebrow: 'Destinations with a good price right now',
			title: 'Real fares, monitored every day.',
			body: 'These are the per-person ranges we have seen in recent weeks, from the cheapest flight to the typical price. Pick a destination and we will quote your exact dates over WhatsApp.',
			ctaLabel: 'Quote this destination',
			updatedPrefix: 'Prices updated on',
			sampleSuffix: 'fares monitored',
			rangeLabel: 'Per person, reference range',
			rangeNote: 'Reference range, subject to availability and dates.',
			fallbackTitle: "Don't see your destination?",
			fallbackBody: 'We quote any route, not just the ones listed here.',
			fallbackCta: 'Ask about another destination',
		},
		servicesHeading: {
			eyebrow: 'What we help with',
			title: 'One trip, many reasons to need it.',
			body: 'Whether it is work, a honeymoon, or a family vacation, we coordinate flights, stays, and pacing with you.',
		},
		services: [
			{
				title: 'Getaways and vacations',
				body: 'Beach, city, or Europe: we put together flights and stays at a fair price without cutting comfort.',
			},
			{
				title: 'Business travel',
				body: 'Itineraries that are quick to coordinate, built around your work schedule.',
			},
			{
				title: 'Weddings, anniversaries, and celebrations',
				body: 'Milestone dates handled with more care in the details: stays, transport, and special touches.',
			},
			{
				title: 'Support in Spanish and English',
				body: 'We coordinate your trip in whichever language works best, ideal for mixed families or groups.',
			},
		],
		processHeading: {
			eyebrow: 'How it works',
			title: 'From idea to ticket, in four steps over WhatsApp.',
			body: 'No long forms and no confusing portals. Everything gets resolved in the conversation.',
		},
		process: [
			{
				step: '01',
				title: 'You message us on WhatsApp',
				body: 'Tell us the destination, rough dates, and how many are traveling. One tap on any destination above does this for you already.',
			},
			{
				step: '02',
				title: 'We send you real options',
				body: 'We check live airline fares and send you the best combinations of price and schedule.',
			},
			{
				step: '03',
				title: 'You confirm and we handle the rest',
				body: 'Stays, transfers, and any extra detail get arranged around your budget and priority.',
			},
			{
				step: '04',
				title: 'You travel with the itinerary in hand',
				body: 'We hand you everything clearly before you leave, and stay available in case anything changes.',
			},
		],
		trustHeading: {
			eyebrow: 'Why book with us',
			title: 'Things you can verify yourself before writing to us.',
			body: 'No empty promises: this is what we actually do differently.',
		},
		trust: [
			{
				title: 'Daily fare monitoring',
				body: 'We check flight prices constantly so we can tell you when it is actually worth buying.',
			},
			{
				title: 'Everything over WhatsApp, no detours',
				body: 'No portals, no accounts to create. Quote, confirm, and travel straight from the chat.',
			},
			{
				title: 'Legal transparency on the site',
				body: 'Privacy notice, terms, and direct contact are always available in the footer.',
			},
		],
		faqHeading: {
			eyebrow: 'Frequently asked questions',
			title: 'Before you write to us, this might help.',
			body: '',
		},
		faq: [
			{
				question: 'Are the prices shown on the site real?',
				answer:
					'Yes. Each range comes from the per-person fares we detected for that route in recent weeks: the first number is the cheapest flight we saw, the second is the typical price. Your final price depends on your exact dates, which is why we confirm everything over WhatsApp before charging anything.',
			},
			{
				question: 'Do you support English speakers?',
				answer: 'Yes, we coordinate your trip in Spanish or English, whichever is more comfortable for you.',
			},
			{
				question: "Can I get a quote for a destination that isn't listed?",
				answer: 'Of course. The list shows destinations with the best price right now, but we quote any route you need.',
			},
			{
				question: 'How do I know my data is protected?',
				answer: 'Our privacy notice explains what information we use and why. You can check it from the footer at any time.',
			},
		],
		cta: {
			title: 'Already know where you want to go?',
			body: 'Message us on WhatsApp and get real flight options for your next trip in minutes.',
			primary: 'Get my quote',
			secondary: 'Read privacy notice',
		},
		footer: {
			blurb:
				'Bilingual travel planning with fares monitored daily and direct coordination over WhatsApp.',
			legal: 'Legal',
			privacy: 'Privacy',
			terms: 'Terms',
			dataDeletion: 'Data deletion',
		},
	},
} as const;

export const privacyPolicyContent = {
	es: {
		title: 'Privacy Policy',
		description:
			'Política de privacidad de Blue Sky Travel para el sitio web y la atención por WhatsApp.',
		intro:
			'Esta política describe cómo Blue Sky Travel obtiene, usa, conserva y protege información relacionada con el sitio y las conversaciones de viaje iniciadas por WhatsApp.',
		contactCard: [
			['Marca comercial', brand.name],
			['Responsable', brand.legalEntity],
			['Correo de privacidad', brand.privacyEmail],
			['WhatsApp', brand.whatsappDisplay],
			['Domicilio', brand.legalAddress],
		],
		sections: [
			{
				title: '1. Identidad del responsable',
				paragraphs: [
					`${brand.legalEntity} es la parte responsable del tratamiento de los datos personales relacionados con el sitio y los servicios de planeación de viajes operados bajo la marca ${brand.name}.`,
					'Antes del lanzamiento definitivo, sustituye el nombre legal y domicilio pendientes por los datos corporativos finales.',
				],
			},
			{
				title: '2. Datos que podemos tratar',
				items: [
					'Nombre, apellido o nombre de perfil.',
					'Número de teléfono y datos de contacto compartidos por WhatsApp.',
					'Correo electrónico y preferencias de contacto, si el cliente los proporciona.',
					'Contenido de mensajes, destino, fechas, presupuesto, número de viajeros y contexto del viaje.',
					'Datos técnicos básicos del sitio, como IP, navegador, páginas visitadas y registros operativos cuando existan.',
				],
			},
			{
				title: '3. Finalidades principales',
				items: [
					'Responder solicitudes de viaje y coordinar una conversación comercial.',
					'Preparar, estructurar y dar seguimiento a cotizaciones o propuestas de viaje.',
					'Dar continuidad a conversaciones en WhatsApp y mejorar el contexto operativo.',
					'Atender solicitudes relacionadas con soporte, agenda, disponibilidad o servicio.',
				],
			},
			{
				title: '4. Finalidades secundarias',
				paragraphs: [
					'Cuando corresponda y exista base válida para ello, la información también podrá usarse para prospección comercial, seguimiento de marketing relacional y mejora de experiencia. El titular puede oponerse a estas finalidades secundarias por los mecanismos indicados en esta política.',
				],
			},
			{
				title: '5. Transferencias y encargados',
				paragraphs: [
					'La operación puede apoyarse en proveedores de mensajería, hosting, automatización, calendarios, hojas de cálculo, analítica y herramientas de IA o productividad. La información solo debe tratarse para finalidades compatibles con la prestación del servicio.',
				],
				items: [
					'Meta y WhatsApp Business Platform para mensajería comercial.',
					'Infraestructura de hosting y reverse proxy para el sitio y automatizaciones.',
					'Herramientas de calendario, documentos y hojas de cálculo para coordinar solicitudes.',
					'Herramientas de apoyo conversacional o IA cuando se habiliten en el flujo operativo.',
				],
			},
			{
				title: '6. Conservación',
				paragraphs: [
					'La información se conserva solo durante el tiempo necesario para atender la solicitud, sostener la relación comercial, dar seguimiento operativo o cumplir obligaciones legales y administrativas aplicables.',
				],
			},
			{
				title: '7. Derechos ARCO, revocación y limitación',
				paragraphs: [
					`El titular puede solicitar acceso, rectificación, cancelación u oposición, así como revocar consentimiento o limitar ciertos usos, enviando una solicitud al correo ${brand.privacyEmail}.`,
					'La solicitud debe incluir nombre, medio de contacto, relación con la información y una descripción clara de lo que se pide.',
				],
			},
			{
				title: '8. Cookies y tecnologías similares',
				paragraphs: [
					'En fase 1 el sitio no requiere formularios ni marketing automation del lado del navegador. Si en el futuro se habilitan cookies analíticas o publicitarias, esta política y el sitio deberán actualizarse para reflejarlo.',
				],
			},
			{
				title: '9. Cambios',
				paragraphs: [
					`Las actualizaciones de esta política se publicarán en ${localizedPaths.privacy.es}.`,
				],
			},
		],
	},
	en: {
		title: 'Privacy Policy',
		description:
			'Privacy policy for Blue Sky Travel covering the website and WhatsApp-based travel assistance.',
		intro:
			'This policy explains how Blue Sky Travel collects, uses, stores, and protects information connected to the website and WhatsApp-led travel conversations.',
		contactCard: [
			['Trade name', brand.name],
			['Responsible party', brand.legalEntity],
			['Privacy email', brand.privacyEmail],
			['WhatsApp', brand.whatsappDisplay],
			['Business address', brand.legalAddress],
		],
		sections: [
			{
				title: '1. Identity of the responsible party',
				paragraphs: [
					`${brand.legalEntity} is the party responsible for processing personal data related to the website and the travel-planning services operated under the ${brand.name} brand.`,
					'Before full production launch, replace the pending legal name and business address with the final corporate details.',
				],
			},
			{
				title: '2. Data we may process',
				items: [
					'Name, surname, or profile name.',
					'Phone number and contact details shared through WhatsApp.',
					'Email address and contact preferences when provided by the traveler.',
					'Message content, destination, dates, budget, traveler count, and trip context.',
					'Basic website technical data such as IP address, browser, visited pages, and operational logs when applicable.',
				],
			},
			{
				title: '3. Primary purposes',
				items: [
					'Respond to travel inquiries and coordinate a commercial conversation.',
					'Prepare, structure, and follow up on quotes or trip proposals.',
					'Continue WhatsApp conversations with better operational context.',
					'Handle support, scheduling, availability, or service-related requests.',
				],
			},
			{
				title: '4. Secondary purposes',
				paragraphs: [
					'Where appropriate and lawfully supported, information may also be used for commercial prospecting, relationship marketing follow-up, and service improvement. Data subjects can object to these secondary purposes through the mechanisms described in this policy.',
				],
			},
			{
				title: '5. Sharing and processors',
				paragraphs: [
					'Operations may rely on messaging, hosting, automation, calendar, spreadsheet, analytics, and productivity or AI providers. Information should only be processed for purposes compatible with service delivery.',
				],
				items: [
					'Meta and the WhatsApp Business Platform for messaging.',
					'Hosting and reverse-proxy infrastructure for the website and automations.',
					'Calendar, document, and spreadsheet tools used to coordinate requests.',
					'Conversation-support or AI tooling when enabled inside operations.',
				],
			},
			{
				title: '6. Retention',
				paragraphs: [
					'Information is kept only for as long as required to handle the request, support the commercial relationship, maintain operations, or comply with applicable legal and administrative obligations.',
				],
			},
			{
				title: '7. Rights, revocation, and limitation of use',
				paragraphs: [
					`Data subjects may request access, correction, deletion, objection, consent revocation, or limitation of certain uses by contacting ${brand.privacyEmail}.`,
					'Requests should include the requester name, contact channel, relationship to the information, and a clear description of the action requested.',
				],
			},
			{
				title: '8. Cookies and similar technologies',
				paragraphs: [
					'Phase 1 does not depend on on-site forms or marketing automation in the browser. If analytics or advertising cookies are enabled later, this policy and the site must be updated accordingly.',
				],
			},
			{
				title: '9. Changes',
				paragraphs: [
					`Updates to this policy will be published at ${localizedPaths.privacy.en}.`,
				],
			},
		],
	},
} as const;

export const termsContent = {
	es: {
		title: 'Términos y contacto legal',
		description:
			'Términos de uso y marco comercial general para Blue Sky Travel.',
		intro:
			'Esta página resume el marco general del sitio, el alcance del servicio y el canal de contacto legal o comercial para Blue Sky Travel.',
		contactCard: [
			['Marca', brand.name],
			['Correo comercial', brand.salesEmail],
			['Correo legal', brand.privacyEmail],
			['WhatsApp', brand.whatsappDisplay],
			['Domicilio', brand.legalAddress],
		],
		sections: [
			{
				title: '1. Alcance del sitio',
				paragraphs: [
					'El sitio tiene una función comercial e informativa. Presenta la propuesta de valor de Blue Sky Travel y dirige la conversación hacia WhatsApp para discovery, cotización o seguimiento.',
				],
			},
			{
				title: '2. Alcance del servicio',
				paragraphs: [
					'Blue Sky Travel ofrece planeación, coordinación y acompañamiento comercial relacionados con viajes. Una cotización, recomendación o propuesta inicial no constituye confirmación definitiva de disponibilidad ni reserva cerrada.',
				],
			},
			{
				title: '3. Disponibilidad y terceros',
				paragraphs: [
					'La disponibilidad final de vuelos, hoteles, experiencias o tarifas depende de proveedores terceros. Las condiciones finales pueden cambiar antes de confirmar una compra o emisión.',
				],
			},
			{
				title: '4. Responsabilidad del viajero',
				items: [
					'Validar nombres, fechas, rutas y cualquier dato sensible antes de confirmar.',
					'Contar con documentación migratoria, sanitaria y financiera necesaria para viajar.',
					'Revisar condiciones aplicables de aerolíneas, hoteles y otros proveedores.',
				],
			},
			{
				title: '5. Uso permitido del sitio',
				items: [
					'No usar el sitio para fines ilícitos o fraudulentos.',
					'No suplantar identidad ni enviar información deliberadamente falsa.',
					'No interferir con la disponibilidad, seguridad o integridad del servicio.',
				],
			},
			{
				title: '6. Cambios',
				paragraphs: [
					'Blue Sky Travel puede actualizar este contenido para reflejar cambios operativos, legales o comerciales. La version vigente sera la publicada en el sitio.',
				],
			},
		],
	},
	en: {
		title: 'Terms and legal contact',
		description: 'General terms of use and contact framework for Blue Sky Travel.',
		intro:
			'This page summarizes the site framework, service scope, and the legal or commercial contact channel for Blue Sky Travel.',
		contactCard: [
			['Brand', brand.name],
			['Sales email', brand.salesEmail],
			['Legal email', brand.privacyEmail],
			['WhatsApp', brand.whatsappDisplay],
			['Business address', brand.legalAddress],
		],
		sections: [
			{
				title: '1. Site scope',
				paragraphs: [
					'The site is commercial and informational in nature. It presents the Blue Sky Travel value proposition and moves the conversation into WhatsApp for discovery, quoting, or follow-up.',
				],
			},
			{
				title: '2. Service scope',
				paragraphs: [
					'Blue Sky Travel provides travel planning, coordination, and commercial guidance. An initial quote, recommendation, or proposal does not by itself confirm final availability or a completed booking.',
				],
			},
			{
				title: '3. Availability and third parties',
				paragraphs: [
					'Final availability for flights, hotels, experiences, or fares depends on third-party suppliers. Final conditions may change before a purchase or ticket issuance is confirmed.',
				],
			},
			{
				title: '4. Traveler responsibilities',
				items: [
					'Validate names, dates, routes, and any sensitive details before confirmation.',
					'Maintain the migration, health, and financial documentation required for travel.',
					'Review the conditions applied by airlines, hotels, and other suppliers.',
				],
			},
			{
				title: '5. Permitted use of the site',
				items: [
					'Do not use the site for unlawful or fraudulent purposes.',
					'Do not impersonate others or submit deliberately false information.',
					'Do not interfere with the availability, security, or integrity of the service.',
				],
			},
			{
				title: '6. Changes',
				paragraphs: [
					'Blue Sky Travel may update this content to reflect operational, legal, or commercial changes. The current version will always be the one published on the site.',
				],
			},
		],
	},
} as const;

export const dataDeletionContent = {
	es: {
		title: 'Eliminación de datos',
		description:
			'Canal para solicitar eliminación o revisión de información relacionada con Blue Sky Travel.',
		intro:
			'Si deseas solicitar la eliminación, corrección o revisión de información relacionada con el sitio o conversaciones por WhatsApp, utiliza este procedimiento.',
		steps: [
			'Envíanos un correo a privacy@blueskytravelmx.com.',
			'Incluye tu nombre, teléfono o medio por el que interactuaste con nosotros.',
			'Describe con precisión si solicitas acceso, corrección, eliminación, oposición o limitación de uso.',
			'Agrega el contexto necesario para identificar tu conversación o solicitud.',
		],
		timing:
			'El tiempo de respuesta y validación final debe alinearse a la política de privacidad y a las obligaciones legales aplicables antes del lanzamiento definitivo.',
	},
	en: {
		title: 'Data deletion',
		description:
			'Contact route to request deletion or review of information related to Blue Sky Travel.',
		intro:
			'If you want to request deletion, correction, or review of information related to the site or WhatsApp conversations, use the following process.',
		steps: [
			'Send an email to privacy@blueskytravelmx.com.',
			'Include your name, phone number, or the channel through which you interacted with us.',
			'Describe clearly whether you are requesting access, correction, deletion, objection, or limitation of use.',
			'Add enough context for us to identify your conversation or request.',
		],
		timing:
			'Final response timing and validation should align with the privacy policy and applicable legal obligations before full launch.',
	},
} as const;
