# Тест обработчика формы с событиями
import native events

func onStart(evt)
	emit "Started"
	return null
end

func onPage(inputs)
	emit "Page " & inputs._page
	return null
end

emit "Initialized"

# Установка обработчиков событий
events.SetHandler(events.Start, ref onStart)
events.SetHandler("page", ref onPage)
events.StartLoop()

emit "Ended"