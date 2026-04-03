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
		title: 'Blue Sky Travel | Viajes premium coordinados por WhatsApp',
		description:
			'Landing page bilingüe para Blue Sky Travel. Planeación de viajes premium, coordinación clara y una experiencia lista para vender por WhatsApp.',
		nav: [
			{ label: 'Servicios', href: '#services' },
			{ label: 'Proceso', href: '#process' },
			{ label: 'FAQ', href: '#faq' },
		],
		languageLabel: 'EN',
		languageHref: localizedPaths.home.en,
		hero: {
			eyebrow: 'Travel design for a faster sales funnel',
			headline:
				'Una experiencia de viajes premium que se siente sólida desde el primer clic.',
			body:
				'Blue Sky Travel convierte mejor cuando la marca, la claridad y el acceso por WhatsApp trabajan juntos. Esta fase crea la base visual, legal y comercial para vender con autoridad.',
			primaryCta: 'Planear por WhatsApp',
			secondaryCta: 'Ver proceso',
			badges: ['Bilingüe', 'WhatsApp-first', 'Sin fricción en el primer contacto'],
			spotlightLabel: 'Vista previa de experiencia',
			spotlightTitle: 'Itinerarios claros, handoff directo y CTA lista para vender.',
			spotlightBody:
				'La homepage organiza discovery, confianza y acción. El cliente entiende el valor, sabe qué esperar y encuentra el siguiente paso sin ruido.',
			spotlightStats: [
				{ label: 'Canal principal', value: 'WhatsApp' },
				{ label: 'Idiomas', value: 'ES / EN' },
				{ label: 'Fase 1', value: 'Homepage + legal' },
			],
			journeyCards: [
				{
					kicker: 'Corporate travel',
					title: 'Coordina viajes ejecutivos sin perder tiempo en explicaciones innecesarias.',
				},
				{
					kicker: 'Celebration travel',
					title: 'Escapadas premium, luna de miel y fechas clave con un tono más elevado.',
				},
				{
					kicker: 'Family planning',
					title: 'Requisitos, ritmo del viaje y decisiones más claras desde el inicio.',
				},
			],
		},
		proof: [
			{
				title: 'Claridad comercial',
				body: 'La propuesta, el proceso y la acción principal se entienden de inmediato.',
			},
			{
				title: 'Tono premium',
				body: 'Visuales, tipografía y mensajes alineados a una marca de viajes de mayor valor.',
			},
			{
				title: 'Salida directa',
				body: 'El sitio prepara la conversación y empuja al canal donde ya operas: WhatsApp.',
			},
		],
		servicesHeading: {
			eyebrow: 'Servicios clave',
			title: 'La página vende mejor cuando el cliente entiende dónde encaja.',
			body:
				'La estructura muestra escenarios concretos de compra para que el usuario se identifique rápido y llegue a WhatsApp con una necesidad mejor definida.',
		},
		services: [
			{
				title: 'Escapadas premium',
				body: 'Curaduría de hoteles, vuelos y ritmo de viaje para clientes que quieren una experiencia más pulida.',
			},
			{
				title: 'Viaje corporativo',
				body: 'Coordinación más clara para ejecutivos, equipos y agendas donde el tiempo importa.',
			},
			{
				title: 'Celebraciones y ocasiones especiales',
				body: 'Luna de miel, aniversarios y viajes importantes con una narrativa más emocional y ordenada.',
			},
			{
				title: 'Planeación bilingüe',
				body: 'Comunicación en español o inglés para viajeros internacionales, clientes mixtos y soporte más flexible.',
			},
		],
		differentiatorsHeading: {
			eyebrow: 'Por qué funciona',
			title: 'No es solo una página bonita. Es una página que organiza la venta.',
			body:
				'Cada bloque reduce fricción: posicionamiento claro, prueba de proceso, rutas de decisión simples y una salida directa al canal de cierre.',
		},
		differentiators: [
			{
				title: 'Discovery mejor guiado',
				body: 'El usuario entiende desde la homepage qué tipo de viaje puede resolver contigo y qué datos conviene llevar a WhatsApp.',
			},
			{
				title: 'Confianza legal visible',
				body: 'Privacy policy, terms y data deletion disponibles desde el footer para pasar Meta y operar con una base más seria.',
			},
			{
				title: 'Arquitectura lista para crecer',
				body: 'La implementación queda preparada para sumar formularios, tracking y entry points más sofisticados en la siguiente fase.',
			},
		],
		processHeading: {
			eyebrow: 'Proceso',
			title: 'Cuatro pasos para mover la conversación desde interés hasta cotización.',
			body:
				'La narrativa de proceso reduce dudas y ayuda a que el primer mensaje por WhatsApp sea más útil para tu equipo o para el agente.',
		},
		process: [
			{
				step: '01',
				title: 'El cliente aterriza en la oferta correcta',
				body: 'La homepage segmenta por necesidad y comunica el valor sin pedir demasiado esfuerzo.',
			},
			{
				step: '02',
				title: 'WhatsApp concentra el discovery',
				body: 'El CTA principal lleva directo al canal donde ya vive la conversación comercial.',
			},
			{
				step: '03',
				title: 'La solicitud llega mas clara',
				body: 'Destino, tono del viaje y contexto se entienden mejor desde el primer intercambio.',
			},
			{
				step: '04',
				title: 'El handoff queda listo para crecer',
				body: 'La base visual y legal queda preparada para conectar formularios, tracking o automatización más adelante.',
			},
		],
		showcaseHeading: {
			eyebrow: 'Escenarios de compra',
			title: 'La página habla con distintos tipos de viaje sin perder coherencia.',
			body:
				'Esto ayuda a vender más de una clase de experiencia sin que el sitio se sienta disperso.',
		},
		showcase: [
			{
				title: 'Corporate itinerary',
				body: 'Viajes ejecutivos con velocidad, claridad y una imagen más seria frente al cliente.',
			},
			{
				title: 'Luxury getaway',
				body: 'Estancias, upgrade de experiencia y tono editorial para tickets más altos.',
			},
			{
				title: 'Family coordination',
				body: 'Viajes con más variables, pero con una estructura de decisión que sigue siendo clara.',
			},
			{
				title: 'Special occasion',
				body: 'Momentos donde el viaje importa emocionalmente y la marca debe verse a la altura.',
			},
		],
		briefHeading: {
			eyebrow: 'Primer mensaje ideal',
			title: 'Qué conviene enviar por WhatsApp para acelerar la cotización.',
			body:
				'La página no obliga formularios en fase 1, pero sí prepara al cliente para llegar mejor orientado.',
		},
		brief: [
			'Destino o idea de viaje.',
			'Fechas o ventana aproximada.',
			'Número de viajeros.',
			'Prioridad principal: lujo, velocidad, presupuesto o celebración.',
		],
		faqHeading: {
			eyebrow: 'FAQ',
			title: 'Dudas que la página debe resolver antes del clic.',
			body: 'Un FAQ corto y directo ayuda a sostener la conversión sin empujar al usuario fuera del flujo.',
		},
		faq: [
			{
				question: '¿Qué pasa cuando escribo por WhatsApp?',
				answer:
					'La conversación se enfoca en entender el tipo de viaje, fechas, destino y contexto para avanzar hacia una cotización o un siguiente paso más claro.',
			},
			{
				question: '¿Puedo atender clientes en inglés?',
				answer:
					'Sí. La homepage y el flujo de marca ya consideran una experiencia bilingüe para sostener conversaciones en español o inglés.',
			},
			{
				question: '¿Esta fase ya incluye un motor de reservas?',
				answer:
					'No. En fase 1 la salida principal es WhatsApp. La estructura queda preparada para integrar formularios, tracking o automatización adicional más adelante.',
			},
			{
				question: '¿La privacy policy ya es suficiente para Meta?',
				answer:
					'La estructura queda lista, pero antes de producción debes sustituir los datos legales pendientes por los definitivos de la empresa.',
			},
		],
		cta: {
			title: 'Si el sitio ya comunica mejor, el siguiente paso debe ser igual de simple.',
			body:
				'Abre WhatsApp y lleva la conversación al canal donde ya estás construyendo el agente y el proceso comercial.',
			primary: 'Abrir WhatsApp',
			secondary: 'Leer privacidad',
		},
		footer: {
			blurb:
				'Planeación de viajes bilingüe diseñada para sostener ventas premium, claridad legal y un handoff más limpio hacia WhatsApp.',
			legal: 'Legal',
			privacy: 'Privacidad',
			terms: 'Términos',
			dataDeletion: 'Eliminación de datos',
		},
	},
	en: {
		title: 'Blue Sky Travel | Premium travel planning built for WhatsApp sales',
		description:
			'Bilingual landing page for Blue Sky Travel. Premium travel planning, clear coordination, and a stronger WhatsApp-first conversion experience.',
		nav: [
			{ label: 'Services', href: '#services' },
			{ label: 'Process', href: '#process' },
			{ label: 'FAQ', href: '#faq' },
		],
		languageLabel: 'ES',
		languageHref: localizedPaths.home.es,
		hero: {
			eyebrow: 'Travel design for a faster sales funnel',
			headline:
				'A premium travel experience that feels credible from the very first click.',
			body:
				'Blue Sky Travel converts better when brand, clarity, and WhatsApp access work together. This phase builds the visual, legal, and commercial foundation needed to sell with confidence.',
			primaryCta: 'Plan on WhatsApp',
			secondaryCta: 'View process',
			badges: ['Bilingual', 'WhatsApp-first', 'Low-friction first contact'],
			spotlightLabel: 'Experience preview',
			spotlightTitle: 'Clear itineraries, direct handoff, and a CTA that is ready to sell.',
			spotlightBody:
				'The homepage organizes discovery, trust, and action. Visitors understand the offer, know what happens next, and can move into WhatsApp without noise.',
			spotlightStats: [
				{ label: 'Primary channel', value: 'WhatsApp' },
				{ label: 'Languages', value: 'ES / EN' },
				{ label: 'Phase 1', value: 'Homepage + legal' },
			],
			journeyCards: [
				{
					kicker: 'Corporate travel',
					title: 'Coordinate executive travel without losing time in preventable back-and-forth.',
				},
				{
					kicker: 'Celebration travel',
					title: 'Premium escapes, honeymoons, and milestone trips with a more elevated tone.',
				},
				{
					kicker: 'Family planning',
					title: 'Handle more variables while keeping the decision path easier to follow.',
				},
			],
		},
		proof: [
			{
				title: 'Commercial clarity',
				body: 'The value proposition, process, and primary action are legible immediately.',
			},
			{
				title: 'Premium tone',
				body: 'Visuals, typography, and messaging support a more valuable travel brand.',
			},
			{
				title: 'Direct handoff',
				body: 'The site prepares the conversation and drives visitors into the channel where you already operate: WhatsApp.',
			},
		],
		servicesHeading: {
			eyebrow: 'Core services',
			title: 'The page sells better when the visitor understands where they fit.',
			body:
				'The structure shows concrete purchase scenarios so visitors can identify themselves quickly and enter WhatsApp with a better-defined need.',
		},
		services: [
			{
				title: 'Premium getaways',
				body: 'Hotel, flight, and pacing curation for clients who want a more polished experience.',
			},
			{
				title: 'Corporate travel',
				body: 'Clearer coordination for executives, teams, and schedules where time matters.',
			},
			{
				title: 'Celebrations and special occasions',
				body: 'Honeymoons, anniversaries, and milestone trips with a more emotional and elevated narrative.',
			},
			{
				title: 'Bilingual planning',
				body: 'Spanish or English communication for international travelers, mixed teams, and more flexible support.',
			},
		],
		differentiatorsHeading: {
			eyebrow: 'Why it works',
			title: 'This is not just a nicer homepage. It is a page that organizes the sale.',
			body:
				'Each block reduces friction: clear positioning, visible process proof, simpler decision paths, and a direct handoff to the closing channel.',
		},
		differentiators: [
			{
				title: 'Better-guided discovery',
				body: 'Visitors understand what kind of trip they can solve with you and what details they should bring into WhatsApp.',
			},
			{
				title: 'Visible legal trust',
				body: 'Privacy policy, terms, and data-deletion pages live in the footer so the stack is ready for Meta and more serious operations.',
			},
			{
				title: 'Ready to scale',
				body: 'The implementation stays ready for forms, tracking, and more advanced entry points in the next phase.',
			},
		],
		processHeading: {
			eyebrow: 'Process',
			title: 'Four steps to move the conversation from interest to quote.',
			body:
				'The process narrative reduces uncertainty and helps the first WhatsApp message arrive with better context for your team or the agent.',
		},
		process: [
			{
				step: '01',
				title: 'The visitor lands on the right offer',
				body: 'The homepage segments by need and communicates value without asking for too much effort.',
			},
			{
				step: '02',
				title: 'WhatsApp concentrates discovery',
				body: 'The primary CTA moves directly into the commercial channel you already use.',
			},
			{
				step: '03',
				title: 'The request arrives with more context',
				body: 'Destination, trip tone, and business context are easier to understand from the first exchange.',
			},
			{
				step: '04',
				title: 'The handoff is ready to grow',
				body: 'The visual and legal foundation is now ready for forms, tracking, or deeper automation later.',
			},
		],
		showcaseHeading: {
			eyebrow: 'Purchase scenarios',
			title: 'The site can speak to different trip types without losing coherence.',
			body:
				'That helps sell more than one class of experience without making the brand feel scattered.',
		},
		showcase: [
			{
				title: 'Corporate itinerary',
				body: 'Executive travel with more speed, clarity, and a more credible client-facing image.',
			},
			{
				title: 'Luxury getaway',
				body: 'Stays, experience upgrades, and editorial tone for higher-ticket opportunities.',
			},
			{
				title: 'Family coordination',
				body: 'Trips with more moving parts, while still keeping the decision path clear.',
			},
			{
				title: 'Special occasion',
				body: 'Moments where the trip carries emotional weight and the brand needs to look the part.',
			},
		],
		briefHeading: {
			eyebrow: 'Best first message',
			title: 'What a visitor should send on WhatsApp to speed up the quote.',
			body:
				'Phase 1 avoids form friction, but it still prepares the visitor to arrive better oriented.',
		},
		brief: [
			'Destination or travel idea.',
			'Dates or an approximate travel window.',
			'Number of travelers.',
			'Primary priority: luxury, speed, budget, or celebration.',
		],
		faqHeading: {
			eyebrow: 'FAQ',
			title: 'Questions the site should answer before the click.',
			body: 'A short and direct FAQ helps hold conversion without pushing the visitor out of the flow.',
		},
		faq: [
			{
				question: 'What happens after I message on WhatsApp?',
				answer:
					'The conversation focuses on understanding the trip type, dates, destination, and context so the next step toward a quote is clearer.',
			},
			{
				question: 'Can you handle English-speaking travelers?',
				answer:
					'Yes. The homepage and brand flow are already structured to support conversations in Spanish or English.',
			},
			{
				question: 'Does phase 1 include a booking engine?',
				answer:
					'No. In phase 1 the primary path is WhatsApp. The architecture stays ready for forms, tracking, and deeper automation later.',
			},
			{
				question: 'Is the privacy policy enough for Meta already?',
				answer:
					'The structure is ready, but before production you still need to replace the pending legal details with the final business information.',
			},
		],
		cta: {
			title: 'If the site explains the offer better, the next step should be just as simple.',
			body:
				'Open WhatsApp and move the conversation into the channel where your sales flow and agent strategy already live.',
			primary: 'Open WhatsApp',
			secondary: 'Read privacy policy',
		},
		footer: {
			blurb:
				'Bilingual travel planning designed to support premium sales, legal clarity, and a cleaner WhatsApp handoff.',
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
